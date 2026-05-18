from collections import Counter, defaultdict

from .prediction_service import ACTION_SCORES


class RecommendationService:
    CUSTOMER_SOURCE_CHANNEL = "customer_page"

    def _customer_personal_logs(self, user_id, logs):
        return [
            log
            for log in logs
            if log.get("user_id") == user_id
            and log.get("source_channel") == self.CUSTOMER_SOURCE_CHANNEL
        ]

    def _build_fallback_items(self, products, hot_scores, limit=5):
        ranked_products = sorted(
            products,
            key=lambda product: (hot_scores.get(product.id, 0), product.stock),
            reverse=True,
        )

        items = []
        for product in ranked_products[:limit]:
            hot_score = hot_scores.get(product.id, 0)
            items.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "reason": f"该商品近期热度分为 {hot_score}，适合作为当前阶段的冷启动推荐",
                }
            )
        return items

    def recommend_for_customer(self, user_id, logs, products):
        if not products:
            return {"mode": "fallback", "items": []}

        interacted_product_ids = set()
        category_counter = Counter()
        hot_scores = defaultdict(int)

        for log in logs:
            score = ACTION_SCORES.get(log["action_type"], 0)
            hot_scores[log["product_id"]] += score

        for log in self._customer_personal_logs(user_id, logs):
            score = ACTION_SCORES.get(log["action_type"], 0)
            category_counter[log["category"]] += score
            interacted_product_ids.add(log["product_id"])

        favorite_category = category_counter.most_common(1)[0][0] if category_counter else None
        if not favorite_category and not interacted_product_ids:
            return {
                "mode": "fallback",
                "items": self._build_fallback_items(products, hot_scores),
            }

        ranked_products = sorted(
            products,
            key=lambda product: (
                1 if product.category == favorite_category else 0,
                hot_scores.get(product.id, 0),
                product.stock,
            ),
            reverse=True,
        )

        items = []
        favorite_category_score = category_counter.get(favorite_category, 0) if favorite_category else 0
        for product in ranked_products:
            if product.id in interacted_product_ids:
                continue

            hot_score = hot_scores.get(product.id, 0)
            if favorite_category and product.category == favorite_category:
                reason = (
                    f"你在 {favorite_category} 类目近期偏好得分为 {favorite_category_score}，"
                    f"该商品热度分为 {hot_score}，适合优先关注"
                )
            elif favorite_category:
                reason = (
                    f"你常看 {favorite_category} 类目（偏好得分 {favorite_category_score}），"
                    f"该商品热度分为 {hot_score}，可作为扩展选择"
                )
            else:
                reason = f"该商品近期热度分为 {hot_score}，适合作为你的入门推荐"

            items.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "reason": reason,
                }
            )

        if not items:
            return {
                "mode": "fallback",
                "items": self._build_fallback_items(products, hot_scores),
            }

        return {"mode": "personalized", "items": items[:5]}
