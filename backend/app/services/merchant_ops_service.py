from datetime import datetime, timedelta
from decimal import Decimal

import random

from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product
from .analytics_service import AnalyticsService


class MerchantOpsService:
    def __init__(self):
        self._brand_display = AnalyticsService.BRAND_DISPLAY

    def _build_color_breakdown(self, product_id, stock):
        stock = int(stock or 0)
        if stock <= 0:
            return []

        colors = ["红", "蓝", "黑", "白", "灰", "绿"]
        rng = random.Random(int(product_id))
        weights = [rng.random() for _ in colors]
        total = sum(weights)
        if total <= 0:
            return [{"color": colors[0], "count": stock}]

        base = [int(stock * (w / total)) for w in weights]
        remainder = stock - sum(base)
        ranked_indices = sorted(range(len(colors)), key=lambda idx: weights[idx], reverse=True)
        for idx in ranked_indices:
            if remainder <= 0:
                break
            base[idx] += 1
            remainder -= 1
        if remainder > 0:
            for idx in ranked_indices:
                if remainder <= 0:
                    break
                base[idx] += 1
                remainder -= 1

        result = [
            {"color": colors[idx], "count": int(base[idx])}
            for idx in ranked_indices
            if int(base[idx]) > 0
        ]
        if sum(item["count"] for item in result) != stock:
            if result:
                result[0]["count"] += stock - sum(item["count"] for item in result)
            else:
                result = [{"color": colors[0], "count": stock}]
        return result

    def build_overview(self, merchant_id, days=30, low_sales_threshold=3, brand_top_n=5):
        days = int(days)
        low_sales_threshold = int(low_sales_threshold)
        brand_top_n = int(brand_top_n)

        threshold = datetime.utcnow() - timedelta(days=days)
        products = Product.query.filter_by(merchant_id=merchant_id).all()
        product_by_id = {item.id: item for item in products}

        purchase_rows = (
            db.session.query(BehaviorLog.product_id, func.count(BehaviorLog.id))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= threshold,
            )
            .group_by(BehaviorLog.product_id)
            .all()
        )
        purchase_by_product = {product_id: count for product_id, count in purchase_rows}

        revenue = Decimal("0.00")
        cost = Decimal("0.00")
        for product_id, count in purchase_by_product.items():
            product = product_by_id.get(product_id)
            if product is None:
                continue
            price = Decimal(str(product.price or 0))
            cost_price = Decimal(str(product.cost_price or 0))
            if cost_price <= 0:
                cost_price = (price * Decimal("0.60")).quantize(Decimal("0.01"))
            revenue += (price * Decimal(count)).quantize(Decimal("0.01"))
            cost += (cost_price * Decimal(count)).quantize(Decimal("0.01"))

        inventory_items = []
        inactive_items = []
        for product in products:
            price = Decimal(str(product.price or 0))
            cost_price = Decimal(str(product.cost_price or 0))
            if cost_price <= 0:
                cost_price = (price * Decimal("0.60")).quantize(Decimal("0.01"))
            item = {
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "brand": self._brand_display.get(product.brand, product.brand),
                "image_url": product.image_url,
                "stock": int(product.stock or 0),
                "price": float(price),
                "cost_price": float(cost_price),
                "is_active": bool(product.is_active),
            }
            item["color_breakdown"] = self._build_color_breakdown(item["product_id"], item["stock"])
            if not product.is_active:
                inactive_items.append(item)
                continue
            if item["stock"] > 0:
                inventory_items.append(item)

        delist_suggestions = []
        for product in products:
            if not product.is_active:
                continue
            purchase_count = int(purchase_by_product.get(product.id, 0))
            if purchase_count < low_sales_threshold:
                delist_suggestions.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "category": product.category,
                        "brand": self._brand_display.get(product.brand, product.brand),
                        "image_url": product.image_url,
                        "purchase_count_30d": purchase_count,
                        "stock": int(product.stock or 0),
                        "price": float(product.price or 0),
                        "color_breakdown": self._build_color_breakdown(product.id, int(product.stock or 0)),
                    }
                )

        brand_counter = {}
        top_product_by_brand = {}
        for product in products:
            count = int(purchase_by_product.get(product.id, 0))
            if count <= 0:
                continue
            brand = self._brand_display.get(product.brand, product.brand)
            brand_counter[brand] = brand_counter.get(brand, 0) + count
            current = top_product_by_brand.get(brand)
            if current is None or count > current["count"]:
                top_product_by_brand[brand] = {"count": count, "name": product.name}
        focus_brands = [
            {
                "brand": brand,
                "purchase_count_30d": count,
                "top_product_name": (top_product_by_brand.get(brand) or {}).get("name", ""),
            }
            for brand, count in sorted(brand_counter.items(), key=lambda item: item[1], reverse=True)[
                :brand_top_n
            ]
        ]

        return {
            "summary": {
                "days": days,
                "revenue": float(revenue),
                "cost": float(cost),
                "profit": float((revenue - cost).quantize(Decimal("0.01"))),
            },
            "inventory_items": inventory_items,
            "delist_suggestions": delist_suggestions,
            "inactive_items": inactive_items,
            "focus_brands": focus_brands,
        }
