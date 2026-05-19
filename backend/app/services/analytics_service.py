from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ..extensions import db
from ..models.daily_metric import DailyProductMetric


FUNNEL_STEPS = ("view", "click", "favorite", "cart", "purchase")
HOT_SCORE_WEIGHTS = {
    "view": 1,
    "click": 2,
    "favorite": 3,
    "cart": 5,
    "purchase": 8,
}
HOT_SCORE_HALF_LIFE_HOURS = 24
MERCHANT_BEHAVIOR_WEIGHTS = {
    "favorite": 3,
    "cart": 5,
    "purchase": 8,
}
MERCHANT_BEHAVIOR_LABELS = {
    "favorite": "收藏",
    "cart": "加购",
    "purchase": "购买",
}


class AnalyticsService:
    BRAND_DISPLAY = {
        "CloudStep": "云步",
        "ActiveWear": "活力穿",
        "UrbanSprint": "城市疾跑",
        "TrailPeak": "峰行",
        "HomeFit": "家健",
        "NutriMax": "营养力",
        "WildCamp": "野营",
        "PowerCore": "力量核心",
        "SoundFly": "声行",
        "FlexPro": "柔韧",
        "CoreUp": "核心力",
        "PulseOne": "脉动一号",
        "AeroRun": "疾风跑",
        "MotionLab": "动能实验室",
        "FuelGo": "燃动",
    }

    @classmethod
    def _brand_display(cls, brand):
        if not brand:
            return "未知品牌"
        return cls.BRAND_DISPLAY.get(brand, brand)
    def _merchant_logs(self, logs, merchant_id=None):
        if merchant_id is None:
            return logs

        return [log for log in logs if log.get("merchant_id") == merchant_id]

    def _action_counter(self, logs):
        return Counter(log["action_type"] for log in logs)

    def build_overview(self, logs, merchant_id=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        action_counter = self._action_counter(scoped_logs)
        unique_users = {log["user_id"] for log in scoped_logs}
        product_counter = Counter(
            (log["product_id"], log["product_name"]) for log in scoped_logs
        )
        region_counter = Counter(log["region"] for log in scoped_logs)
        view_count = action_counter.get("view", 0)
        purchase_count = action_counter.get("purchase", 0)
        purchase_rate = (purchase_count + 1) / (view_count + 2) if view_count else 0

        return {
            "totals": {
                "behavior_count": len(scoped_logs),
                "view_count": view_count,
                "uv": len(unique_users),
                "purchase_count": purchase_count,
                "purchase_rate": round(purchase_rate, 4),
            },
            "funnel": {
                step: action_counter.get(step, 0)
                for step in FUNNEL_STEPS
            },
            "top_products": [
                {
                    "product_id": product_id,
                    "product_name": product_name,
                    "count": count,
                }
                for (product_id, product_name), count in product_counter.most_common(10)
            ],
            "regions": [
                {"region": region, "count": count}
                for region, count in region_counter.most_common(10)
            ],
        }

    def build_funnel(self, logs, merchant_id=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        action_counter = self._action_counter(scoped_logs)
        return {
            "items": [
                {"key": step, "label": step, "value": action_counter.get(step, 0)}
                for step in FUNNEL_STEPS
            ]
        }

    def build_regions(self, logs, merchant_id=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        region_counter = Counter(log["region"] for log in scoped_logs)
        return {
            "items": [
                {"region": region, "count": count}
                for region, count in region_counter.most_common(10)
            ]
        }

    def build_categories(self, logs, merchant_id=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        category_counter = Counter(log["category"] for log in scoped_logs)
        return {
            "items": [
                {"category": category, "count": count}
                for category, count in category_counter.most_common(10)
            ]
        }

    def build_brands(self, logs, merchant_id=None, category=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        if category:
            scoped_logs = [log for log in scoped_logs if log.get("category") == category]
        brand_counter = Counter(self._brand_display(log.get("brand")) for log in scoped_logs)
        return {
            "items": [
                {"brand": brand, "count": count}
                for brand, count in brand_counter.most_common(10)
            ]
        }

    def _build_product_scores(self, logs, merchant_id=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        latest_timestamp = None
        parsed_timestamps = {}
        for log in scoped_logs:
            raw_timestamp = log.get("timestamp")
            if not raw_timestamp:
                continue
            try:
                parsed = (
                    raw_timestamp
                    if isinstance(raw_timestamp, datetime)
                    else datetime.fromisoformat(raw_timestamp)
                )
            except Exception:
                continue
            parsed_timestamps[id(log)] = parsed
            if latest_timestamp is None or parsed > latest_timestamp:
                latest_timestamp = parsed

        product_scores = defaultdict(
            lambda: {"product_id": None, "product_name": "", "hot_score": 0, "count": 0}
        )
        for log in scoped_logs:
            item = product_scores[log["product_id"]]
            item["product_id"] = log["product_id"]
            item["product_name"] = log["product_name"]
            item["count"] += 1
            weight = HOT_SCORE_WEIGHTS.get(log["action_type"], 0)
            if weight <= 0:
                continue
            decay = 1.0
            if latest_timestamp is not None:
                parsed = parsed_timestamps.get(id(log))
                if parsed is not None:
                    delta_hours = max(
                        (latest_timestamp - parsed).total_seconds() / 3600.0, 0.0
                    )
                    decay = 0.5 ** (delta_hours / HOT_SCORE_HALF_LIFE_HOURS)
            item["hot_score"] += weight * decay

        for item in product_scores.values():
            item["hot_score"] = round(float(item["hot_score"]), 2)
        return list(product_scores.values())

    def build_hot_products(self, logs, merchant_id=None):
        items = sorted(
            self._build_product_scores(logs, merchant_id=merchant_id),
            key=lambda item: (item["hot_score"], item["count"]),
            reverse=True,
        )
        return {"items": items[:10]}

    def build_cold_products(self, logs, merchant_id=None):
        items = sorted(
            self._build_product_scores(logs, merchant_id=merchant_id),
            key=lambda item: (item["hot_score"], item["count"], item["product_name"]),
        )
        return {"items": items[:10]}

    def build_user_rfm(self, logs, merchant_id=None):
        scoped_logs = self._merchant_logs(logs, merchant_id)
        if not scoped_logs:
            return {"items": []}

        parsed_logs = []
        latest_timestamp = None
        for log in scoped_logs:
            timestamp = datetime.fromisoformat(log["timestamp"])
            parsed_logs.append((log, timestamp))
            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp

        user_stats = defaultdict(
            lambda: {"user_id": None, "recency_days": 0, "frequency": 0, "monetary": 0.0}
        )
        for log, timestamp in parsed_logs:
            stats = user_stats[log["user_id"]]
            stats["user_id"] = log["user_id"]
            if log["action_type"] == "purchase":
                stats["frequency"] += 1
                stats["monetary"] += float(log.get("price", 0) or 0)
            recency_days = (latest_timestamp - timestamp).days
            if stats["recency_days"] == 0 or recency_days < stats["recency_days"]:
                stats["recency_days"] = recency_days

        items = []
        for stats in user_stats.values():
            if stats["frequency"] >= 2 and stats["monetary"] >= 500:
                label = "高价值用户"
            elif stats["frequency"] >= 1:
                label = "潜力转化用户"
            else:
                label = "待激活用户"
            items.append(
                {
                    "user_id": stats["user_id"],
                    "recency_days": stats["recency_days"],
                    "frequency": stats["frequency"],
                    "monetary": round(stats["monetary"], 2),
                    "rfm_label": label,
                }
            )

        items.sort(key=lambda item: (item["frequency"], item["monetary"]), reverse=True)
        return {"items": items}

    def _recent_window_logs(self, logs, hours=24):
        if not logs:
            return []

        latest_timestamp = max(datetime.fromisoformat(log["timestamp"]) for log in logs)
        threshold = latest_timestamp - timedelta(hours=hours)
        return [
            log
            for log in logs
            if datetime.fromisoformat(log["timestamp"]) >= threshold
        ]

    def build_merchant_user_behavior(self, merchant_id, logs):
        recent_logs = self._recent_window_logs(logs, hours=24)
        category_stats = defaultdict(
            lambda: {"category": "", "scores": defaultdict(int)}
        )
        product_stats = defaultdict(
            lambda: {"product_id": None, "product_name": "", "scores": defaultdict(int)}
        )

        for log in recent_logs:
            if log.get("merchant_id") != merchant_id:
                continue

            action_type = log.get("action_type")
            if action_type not in MERCHANT_BEHAVIOR_WEIGHTS:
                continue

            category = log.get("category") or ""
            category_item = category_stats[category]
            category_item["category"] = category
            category_item["scores"][action_type] += 1

            product_id = log.get("product_id")
            product_item = product_stats[product_id]
            product_item["product_id"] = product_id
            product_item["product_name"] = log.get("product_name") or ""
            product_item["scores"][action_type] += 1

        preference_changes = []
        for item in category_stats.values():
            top_action, action_count = max(
                item["scores"].items(),
                key=lambda pair: (MERCHANT_BEHAVIOR_WEIGHTS.get(pair[0], 0), pair[1]),
            )
            action_label = MERCHANT_BEHAVIOR_LABELS.get(top_action, top_action)
            preference_changes.append(
                {
                    "category": item["category"],
                    "top_action": top_action,
                    "action_count": action_count,
                    "summary": f"{item['category']}最近{action_label}行为更活跃",
                }
            )

        intent_products = []
        for item in product_stats.values():
            top_action, action_count = max(
                item["scores"].items(),
                key=lambda pair: (MERCHANT_BEHAVIOR_WEIGHTS.get(pair[0], 0), pair[1]),
            )
            action_label = MERCHANT_BEHAVIOR_LABELS.get(top_action, top_action)
            intent_products.append(
                {
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "top_action": top_action,
                    "action_count": action_count,
                    "summary": f"{item['product_name']}最近{action_label}较多，值得重点关注",
                }
            )

        preference_changes.sort(
            key=lambda item: (
                MERCHANT_BEHAVIOR_WEIGHTS.get(item["top_action"], 0),
                item["action_count"],
                item["category"],
            ),
            reverse=True,
        )
        intent_products.sort(
            key=lambda item: (
                MERCHANT_BEHAVIOR_WEIGHTS.get(item["top_action"], 0),
                item["action_count"],
                item["product_name"],
            ),
            reverse=True,
        )

        return {
            "preference_changes": preference_changes[:5],
            "intent_products": intent_products[:5],
        }

    def build_daily_product_metrics(self, logs):
        grouped = {}

        for log in logs:
            metric_date = datetime.fromisoformat(log["timestamp"]).date()
            key = (log["product_id"], metric_date)
            payload = grouped.setdefault(
                key,
                {
                    "product_id": log["product_id"],
                    "product_name": log["product_name"],
                    "metric_date": metric_date,
                    "view_count": 0,
                    "click_count": 0,
                    "favorite_count": 0,
                    "cart_count": 0,
                    "purchase_count": 0,
                },
            )

            action_key = f'{log["action_type"]}_count'
            if action_key in payload:
                payload[action_key] += 1

        rows = []
        for payload in grouped.values():
            view_count = payload["view_count"]
            purchase_count = payload["purchase_count"]
            payload["conversion_rate"] = (
                (purchase_count + 1) / (view_count + 2) if view_count else 0.0
            )
            payload["hot_score"] = sum(
                payload[f"{action}_count"] * weight
                for action, weight in HOT_SCORE_WEIGHTS.items()
            )
            rows.append(payload)

        rows.sort(key=lambda item: (item["metric_date"], item["product_id"]))
        return rows

    def persist_daily_metrics(self, logs):
        rows = self.build_daily_product_metrics(logs)

        for payload in rows:
            metric = DailyProductMetric.query.filter_by(
                product_id=payload["product_id"],
                metric_date=payload["metric_date"],
            ).first()
            if metric is None:
                metric = DailyProductMetric(
                    product_id=payload["product_id"],
                    metric_date=payload["metric_date"],
                )
                db.session.add(metric)

            metric.product_name = payload["product_name"]
            metric.view_count = payload["view_count"]
            metric.click_count = payload["click_count"]
            metric.favorite_count = payload["favorite_count"]
            metric.cart_count = payload["cart_count"]
            metric.purchase_count = payload["purchase_count"]
            metric.conversion_rate = payload["conversion_rate"]
            metric.hot_score = payload["hot_score"]

        db.session.commit()
        return len(rows)
