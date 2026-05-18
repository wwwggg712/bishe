from .prediction_service import ACTION_SCORES


class StrategyService:
    def build_for_merchant(self, merchant_id, logs):
        product_stats = {}

        for log in logs:
            if log["merchant_id"] != merchant_id:
                continue

            stats = product_stats.setdefault(
                log["product_id"],
                {
                    "product_id": log["product_id"],
                    "product_name": log["product_name"],
                    "views": 0,
                    "purchases": 0,
                    "hot_score": 0,
                },
            )
            stats["hot_score"] += ACTION_SCORES.get(log["action_type"], 0)
            if log["action_type"] == "view":
                stats["views"] += 1
            if log["action_type"] == "purchase":
                stats["purchases"] += 1

        items = []
        for stats in product_stats.values():
            purchase_rate = stats["purchases"] / stats["views"] if stats["views"] else 0
            if stats["views"] >= 2 and purchase_rate < 0.2:
                items.append(
                    {
                        "product_id": stats["product_id"],
                        "product_name": stats["product_name"],
                        "level": "warning",
                        "action": "建议优化详情页并尝试限时促销，提升浏览到购买的转化率",
                        "views": stats["views"],
                        "purchase_rate": round(purchase_rate, 4),
                    }
                )
            elif stats["purchases"] > 0:
                items.append(
                    {
                        "product_id": stats["product_id"],
                        "product_name": stats["product_name"],
                        "level": "info",
                        "action": "该商品已产生购买，建议继续保持曝光并关注库存补货节奏",
                        "views": stats["views"],
                        "purchase_rate": round(purchase_rate, 4),
                    }
                )

        items.sort(key=lambda row: (row["level"] == "warning", row["views"]), reverse=True)
        return {"items": items}
