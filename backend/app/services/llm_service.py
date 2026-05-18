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
                        "content": "你是电商经营分析助手，请结合结构化结果给出简洁专业的中文总结。",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
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

        return (
            f"AI 经营分析认为，当前经营重点应放在 {product_name}，其热度分为 {hot_score}，"
            f"当前整体转化率约为 {purchase_rate:.2%}。"
            f"当前重点类目集中在 {category_name}，同时存在 {anomaly_count} 条异常预警和 "
            f"{cold_product_count} 个冷门商品待处理，建议优先优化高流量低转化商品详情页，并同步调整活动曝光。"
        )

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
