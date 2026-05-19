import json
import os
from urllib import request as urllib_request


class LLMService:
    def build_report(self, payload):
        config = self._provider_config()
        if config is not None:
            try:
                return self._call_provider(payload, config)
            except Exception as error:
                return {
                    "summary": self._build_fallback_summary(payload),
                    "mode": "error",
                    "provider": config["provider"],
                    "model": config["model"],
                    "base_url": config["base_url"],
                    "error_message": str(error),
                }

        return {
            "summary": self._build_fallback_summary(payload),
            "mode": "fallback",
            "provider": "internal",
            "model": "rule-based-fallback",
        }

    def _provider_config(self):
        provider = os.getenv("LLM_PROVIDER", "").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        base_url = os.getenv("LLM_BASE_URL", "").strip()
        model = os.getenv("LLM_MODEL", "").strip()

        if not provider or not api_key or not base_url or not model:
            return None

        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
        }

    def _build_prompt(self, payload):
        scene = payload.get("scene", "general")
        return json.dumps({"scene": scene, "payload": payload}, ensure_ascii=False)

    def _call_provider(self, payload, config):
        prompt = self._build_prompt(payload)
        request_body = json.dumps(
            {
                "model": config["model"],
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是电商经营分析助手。请基于用户提供的结构化数据输出【更长、更有条理】的中文经营分析。"
                            "必须满足："
                            "1）只输出纯文本，不要使用任何 Markdown（不要出现 **、#、-、``` 等符号）。"
                            "2）按以下小节输出并换行分隔："
                            "【核心结论】不超过 2 行，每行不超过 35 字；"
                            "【机会点】至少 3 条，每条单独一行，使用 1）2）3）编号；"
                            "【风险预警】至少 3 条，每条单独一行，使用 1）2）3）编号；"
                            "【行动清单】至少 5 条，每条单独一行，使用 1）2）3）编号；不要出现 P0/P1/P2 等优先级字母。"
                            "3）避免空泛套话，尽量引用数据里的商品名、类目、热度、转化、异常数量等。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 900,
            }
        ).encode("utf-8")

        req = urllib_request.Request(
            config["base_url"],
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['api_key']}",
            },
            method="POST",
        )

        with urllib_request.urlopen(req, timeout=20) as response:
            payload_json = json.loads(response.read().decode("utf-8"))

        summary = payload_json["choices"][0]["message"]["content"].strip()
        return {
            "summary": summary,
            "mode": "provider",
            "provider": config["provider"],
            "model": config["model"],
            "base_url": config["base_url"],
        }

    def _build_fallback_summary(self, payload):
        scene = payload.get("scene")
        if scene == "merchant":
            return self._build_merchant_summary(payload)
        if scene == "customer":
            return self._build_customer_summary(payload)

        product_name = payload.get("product_name", "未知商品")
        hot_score = payload.get("hot_score", 0)
        trend_label = payload.get("trend_label", "flat")
        purchase_rate = float(payload.get("purchase_rate", 0))

        return (
            f"商品 {product_name} 当前热度分为 {hot_score}，"
            f"趋势判断为 {trend_label}，购买转化率为 {purchase_rate:.2%}。"
            "建议结合人群、地区与渠道表现持续优化投放和促销策略。"
        )

    def _build_merchant_summary(self, payload):
        product_name = payload.get("product_name", "重点商品")
        hot_score = payload.get("hot_score", 0)
        purchase_rate = float(payload.get("purchase_rate", 0))
        anomaly_count = payload.get("anomaly_count", 0)
        cold_product_count = payload.get("cold_product_count", 0)
        category_name = payload.get("category_name", "综合类目")

        core_line_1 = (
            f"核心结论：经营重点商品 {product_name} 热度 {hot_score}，整体转化率约 {purchase_rate:.2%}。"
        )
        core_line_2 = (
            f"核心结论：经营类目 {category_name}，异常 {anomaly_count} 条，冷门商品 {cold_product_count} 个。"
        )
        opportunity_lines = [
            "机会点：1）优先提升重点商品转化（主图、卖点、评价与促销联动）。",
            "机会点：2）用重点商品带动关联品曝光（搭配购/加价购/组合券）。",
            "机会点：3）对高浏览低转化商品做定位排查（价格/库存/详情页/支付链路）。",
        ]
        risk_lines = [
            "风险预警：1）异常预警需要每日复盘，避免流量突增但转化下滑。",
            "风险预警：2）冷门商品过多会拖累库存周转，需设置下架与清仓策略。",
            "风险预警：3）类目结构失衡可能影响推荐权重，需均衡供给。",
        ]
        action_lines = [
            "行动清单：1）优化重点商品详情页与价格锚点，提升购买率。",
            "行动清单：2）设置重点商品联动活动，带动低动销商品去化。",
            "行动清单：3）建立异常监控阈值与每日复盘机制。",
            "行动清单：4）对冷门商品做清仓/下架分流，减少库存占用。",
            "行动清单：5）复盘类目与品牌结构，补齐高需求款式供给。",
        ]

        return "\n".join([core_line_1, core_line_2, *opportunity_lines, *risk_lines, *action_lines])

    def _build_customer_summary(self, payload):
        product_name = payload.get("product_name", "推荐商品")
        trend_product_name = payload.get("trend_product_name", "趋势商品")
        preferred_category = payload.get("preferred_category", "综合类目")
        price_band = payload.get("price_band", "综合消费偏好")
        active_hour = payload.get("active_hour", "晚间")

        return (
            f"AI 推荐解释认为，你最近更偏好 {preferred_category} 与 {price_band} 区间商品，"
            f"通常会在 {active_hour} 更活跃，因此优先推荐 {product_name}。"
            f"同时，{trend_product_name} 正处于热度上升阶段，也值得近期继续关注。"
        )
