from decimal import Decimal

from ..models.product import Product
from ..services.analytics_service import AnalyticsService


class PriceCompareService:
    PLATFORMS = ("抖音", "京东", "拼多多", "得物")
    PLATFORM_HINTS = {
        "京东": ("次日达/自营", "可叠加满减券"),
        "拼多多": ("百亿补贴", "大促券可能更低"),
        "抖音": ("直播券", "关注直播间福利"),
        "得物": ("鉴别保障", "正品安心"),
    }
    FACTOR_RANGES = {
        "抖音": (Decimal("0.92"), Decimal("1.08")),
        "京东": (Decimal("0.95"), Decimal("1.12")),
        "拼多多": (Decimal("0.88"), Decimal("1.05")),
        "得物": (Decimal("0.97"), Decimal("1.15")),
    }

    def _factor(self, product_id, platform):
        low, high = self.FACTOR_RANGES[platform]
        span = high - low
        bucket = Decimal(str((product_id * 37 + len(platform) * 11) % 100)) / Decimal(
            "100"
        )
        return (low + span * bucket).quantize(Decimal("0.0001"))

    def build(self, product_id):
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if product is None:
            return None
        base_price = Decimal(str(product.price or 0)).quantize(Decimal("0.01"))

        offers = []
        for platform in self.PLATFORMS:
            factor = self._factor(product_id, platform)
            price = (base_price * factor).quantize(Decimal("0.01"))
            delivery_hint, coupon_hint = self.PLATFORM_HINTS.get(platform, ("", ""))
            offers.append(
                {
                    "platform": platform,
                    "price": float(price),
                    "delivery_hint": delivery_hint,
                    "coupon_hint": coupon_hint,
                }
            )

        best_offer = min(offers, key=lambda item: item["price"])
        saving = (base_price - Decimal(str(best_offer["price"]))).quantize(Decimal("0.01"))
        saving_value = float(max(saving, Decimal("0.00")))

        advice = (
            f"{best_offer['platform']} 当前更便宜，预计可省 {saving_value:.2f} 元；"
            f"若更看重保障与体验，可优先考虑 京东/得物。"
        )

        return {
            "product": {
                "product_id": product.id,
                "name": product.name,
                "price": float(base_price),
                "brand": AnalyticsService._brand_display(product.brand),
                "category": product.category,
                "image_url": product.image_url or "",
            },
            "offers": offers,
            "best": {
                "platform": best_offer["platform"],
                "price": best_offer["price"],
                "saving": saving_value,
            },
            "advice": advice,
        }

