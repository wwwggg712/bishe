from collections import Counter, defaultdict

from .prediction_service import ACTION_SCORES
from .analytics_service import AnalyticsService


class RecommendationService:
    CUSTOMER_SOURCE_CHANNEL = "customer_page"
    def _enrich_item(self, item, product):
        if product is None:
            item.update({"price": 0, "brand": "未知品牌", "image_url": ""})
            return item
        item.update(
            {
                "price": float(product.price or 0),
                "brand": AnalyticsService._brand_display(getattr(product, "brand", None)),
                "image_url": getattr(product, "image_url", "") or "",
            }
        )
        return item

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
        product_by_id = {product.id: product for product in products}

        items = []
        for product in ranked_products[:limit]:
            hot_score = hot_scores.get(product.id, 0)
            item = {
                "product_id": product.id,
                "product_name": product.name,
                "category": product.category,
                "reason": f"该商品近期热度分为 {hot_score}，适合作为当前阶段的冷启动推荐",
            }
            items.append(self._enrich_item(item, product_by_id.get(product.id)))
        return items

    def recommend_for_customer(self, user_id, logs, products):
        if not products:
            return {"mode": "fallback", "items": []}
        product_by_id = {product.id: product for product in products}

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
                self._enrich_item(
                    {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "reason": reason,
                    },
                    product_by_id.get(product.id),
                )
            )

        if not items:
            return {
                "mode": "fallback",
                "items": self._build_fallback_items(products, hot_scores),
            }

        return {"mode": "personalized", "items": items[:5]}
