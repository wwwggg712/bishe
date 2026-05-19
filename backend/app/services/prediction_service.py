from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt


ACTION_SCORES = {
    "view": 1,
    "click": 2,
    "favorite": 3,
    "cart": 5,
    "purchase": 8,
}


class PredictionService:
    CUSTOMER_SOURCE_CHANNEL = "customer_page"

    def _parse_logs(self, logs):
        parsed_logs = []
        latest_timestamp = None

        for log in logs:
            timestamp = datetime.fromisoformat(log["timestamp"])
            parsed_logs.append((log, timestamp))
            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp

        return parsed_logs, latest_timestamp

    def _build_windows(self, latest_timestamp):
        recent_start = latest_timestamp - timedelta(days=2)
        previous_start = recent_start - timedelta(days=3)
        return recent_start, previous_start

    def _relative_ratio(self, current_value, baseline_value):
        return round(current_value / max(baseline_value, 1), 2)

    def _severity_from_ratio(self, ratio):
        if ratio >= 3:
            return "high"
        if ratio >= 2:
            return "medium"
        return "low"

    def build_trends(self, logs):
        if not logs:
            return {"items": []}

        parsed_logs, latest_timestamp = self._parse_logs(logs)
        recent_start, previous_start = self._build_windows(latest_timestamp)
        scores = defaultdict(
            lambda: {
                "product_id": None,
                "product_name": "",
                "current_score": 0,
                "previous_score": 0,
            }
        )

        for log, timestamp in parsed_logs:
            key = log["product_id"]
            item = scores[key]
            item["product_id"] = log["product_id"]
            item["product_name"] = log["product_name"]
            score = ACTION_SCORES.get(log["action_type"], 0)

            if timestamp >= recent_start:
                item["current_score"] += score
            elif timestamp >= previous_start:
                item["previous_score"] += score

        items = []
        for item in scores.values():
            delta = item["current_score"] - item["previous_score"]
            if delta > 0:
                trend_label = "up"
            elif delta < 0:
                trend_label = "down"
            else:
                trend_label = "flat"

            items.append(
                {
                    **item,
                    "delta": delta,
                    "trend_label": trend_label,
                }
            )

        items.sort(key=lambda row: (row["delta"], row["current_score"]), reverse=True)
        return {"items": items}

    def _build_empty_portrait(self):
        return {
            "is_cold_start": True,
            "top_categories": [],
            "top_actions": [],
            "recent_activity": [],
            "engagement_score": 0,
            "top_active_hours": [],
            "price_preference": {
                "average_price": 0,
                "price_band": "暂无数据",
            },
            "profile_tags": [],
        }

    def _build_price_band(self, average_price):
        if average_price >= 400:
            return "高消费偏好"
        if average_price >= 200:
            return "中高消费偏好"
        if average_price >= 100:
            return "大众消费偏好"
        if average_price > 0:
            return "低价敏感型"
        return "暂无数据"

    def _select_price_logs(self, user_logs):
        purchase_logs = [log for log, _ in user_logs if log["action_type"] == "purchase"]
        if purchase_logs:
            return purchase_logs

        intent_logs = [
            log
            for log, _ in user_logs
            if log["action_type"] in {"cart", "favorite"}
        ]
        if intent_logs:
            return intent_logs

        return []

    def _customer_personal_logs(self, user_id, parsed_logs):
        return [
            (log, timestamp)
            for log, timestamp in parsed_logs
            if log["user_id"] == user_id
            and log.get("source_channel") == self.CUSTOMER_SOURCE_CHANNEL
        ]

    def build_user_portrait(self, user_id, logs, top_categories=3, top_actions=5, recent_activity=5):
        if not logs:
            return self._build_empty_portrait()

        parsed_logs, _ = self._parse_logs(logs)
        user_logs = self._customer_personal_logs(user_id, parsed_logs)

        if not user_logs:
            return self._build_empty_portrait()

        category_stats = defaultdict(lambda: {"category": "", "count": 0, "score": 0})
        action_stats = defaultdict(lambda: {"action_type": "", "count": 0, "score": 0})
        recent_items = []
        active_hours = defaultdict(int)
        total_score = 0

        for log, timestamp in user_logs:
            score = ACTION_SCORES.get(log["action_type"], 0)
            total_score += score
            active_hours[timestamp.hour] += 1

            category_item = category_stats[log["category"]]
            category_item["category"] = log["category"]
            category_item["count"] += 1
            category_item["score"] += score

            action_item = action_stats[log["action_type"]]
            action_item["action_type"] = log["action_type"]
            action_item["count"] += 1
            action_item["score"] += score

            recent_items.append(
                {
                    "log_id": log["log_id"],
                    "product_id": log["product_id"],
                    "product_name": log["product_name"],
                    "category": log["category"],
                    "action_type": log["action_type"],
                    "timestamp": timestamp.isoformat(),
                }
            )

        top_categories = sorted(
            category_stats.values(),
            key=lambda item: (item["score"], item["count"], item["category"]),
            reverse=True,
        )[:top_categories]
        top_actions = sorted(
            action_stats.values(),
            key=lambda item: (item["score"], item["count"], item["action_type"]),
            reverse=True,
        )[:top_actions]
        recent_items.sort(key=lambda item: item["timestamp"], reverse=True)
        hour_items = sorted(
            ({"hour": hour, "count": count} for hour, count in active_hours.items()),
            key=lambda item: (item["count"], item["hour"]),
            reverse=True,
        )[:3]
        price_logs = self._select_price_logs(user_logs)
        total_price = sum(float(log.get("price", 0) or 0) for log in price_logs)
        average_price = round(total_price / len(price_logs), 2) if price_logs else 0
        primary_category = top_categories[0]["category"] if top_categories else None
        profile_tags = []
        if primary_category:
            profile_tags.append(f"{primary_category}偏好")
        if hour_items:
            profile_tags.append(f"{hour_items[0]['hour']}点活跃")
        profile_tags.append(self._build_price_band(average_price))

        return {
            "is_cold_start": False,
            "top_categories": top_categories,
            "top_actions": top_actions,
            "recent_activity": recent_items[:recent_activity],
            "engagement_score": total_score,
            "top_active_hours": hour_items,
            "price_preference": {
                "average_price": average_price,
                "price_band": self._build_price_band(average_price),
            },
            "profile_tags": profile_tags,
        }

    def build_profile(self, user_id, logs):
        return {
            "profile": self.build_user_portrait(user_id, logs),
        }

    def build_anomalies(self, logs, merchant_id=None):
        if merchant_id is not None:
            logs = [log for log in logs if log.get("merchant_id") == merchant_id]
        if not logs:
            return {"items": []}

        parsed_logs, latest_timestamp = self._parse_logs(logs)
        recent_start, previous_start = self._build_windows(latest_timestamp)
        product_stats = defaultdict(
            lambda: {
                "product_id": None,
                "product_name": "",
                "baseline": defaultdict(int),
                "current": defaultdict(int),
            }
        )
        region_views = defaultdict(lambda: {"baseline": 0, "current": 0})

        for log, timestamp in parsed_logs:
            bucket = None
            if timestamp >= recent_start:
                bucket = "current"
            elif timestamp >= previous_start:
                bucket = "baseline"

            if not bucket:
                continue

            stats = product_stats[log["product_id"]]
            stats["product_id"] = log["product_id"]
            stats["product_name"] = log["product_name"]
            stats[bucket][log["action_type"]] += 1

            if log["action_type"] == "view":
                region_views[log["region"]][bucket] += 1

        items = []

        for stats in product_stats.values():
            baseline_views = stats["baseline"]["view"]
            current_views = stats["current"]["view"]
            baseline_purchases = stats["baseline"]["purchase"]
            current_purchases = stats["current"]["purchase"]
            baseline_rate = baseline_purchases / baseline_views if baseline_views else 0
            current_rate = current_purchases / current_views if current_views else 0
            traffic_ratio = self._relative_ratio(current_views, baseline_views)
            z_score = (current_views - baseline_views) / sqrt(max(baseline_views, 1))

            if current_views >= 3 and z_score >= 2.0 and current_rate <= baseline_rate:
                baseline = baseline_views
                current_value = current_views
                delta = current_value - baseline
                items.append(
                    {
                        "type": "traffic_spike_low_conversion",
                        "target": stats["product_name"],
                        "metric": "view",
                        "current_value": current_value,
                        "baseline": baseline,
                        "baseline_value": baseline,
                        "delta": delta,
                        "change_ratio": traffic_ratio,
                        "z_score": round(z_score, 2),
                        "severity": self._severity_from_ratio(traffic_ratio),
                        "reason": (
                            f"{stats['product_name']} 最近浏览量从 {baseline} 增长到 {current_value}，"
                            "但转化率未同步提升，疑似高流量低转化。"
                        ),
                    }
                )

            current_favorites = stats["current"]["favorite"]
            current_carts = stats["current"]["cart"]
            favorite_ratio = self._relative_ratio(current_favorites, current_carts)
            if current_favorites >= 2 and current_carts < current_favorites:
                baseline = current_carts
                current_value = current_favorites
                delta = current_value - baseline
                items.append(
                    {
                        "type": "favorite_high_cart_low",
                        "target": stats["product_name"],
                        "metric": "favorite",
                        "current_value": current_value,
                        "baseline": baseline,
                        "baseline_value": baseline,
                        "delta": delta,
                        "change_ratio": favorite_ratio,
                        "severity": self._severity_from_ratio(favorite_ratio),
                        "reason": (
                            f"{stats['product_name']} 收藏量为 {current_value}，但加购量仅 {baseline}，"
                            "说明兴趣较高但下单意愿偏弱。"
                        ),
                    }
                )

        for region, values in region_views.items():
            traffic_ratio = self._relative_ratio(values["current"], values["baseline"])
            if values["current"] >= 3 and traffic_ratio >= 2:
                baseline = values["baseline"]
                current_value = values["current"]
                delta = current_value - baseline
                items.append(
                    {
                        "type": "region_traffic_spike",
                        "target": region,
                        "metric": "view",
                        "current_value": current_value,
                        "baseline": baseline,
                        "baseline_value": baseline,
                        "delta": delta,
                        "change_ratio": traffic_ratio,
                        "severity": self._severity_from_ratio(traffic_ratio),
                        "reason": (
                            f"{region} 地区近期浏览量从 {baseline} 上升到 {current_value}，"
                            "建议关注区域投放和库存配置。"
                        ),
                    }
                )

        severity_order = {"high": 2, "medium": 1, "low": 0}
        items.sort(
            key=lambda item: (
                severity_order.get(item["severity"], 0),
                item["change_ratio"],
                item["current_value"],
            ),
            reverse=True,
        )
        return {"items": items}
