from datetime import datetime, timedelta

from sqlalchemy import func

from ..extensions import db
from ..models.behavior_log import BehaviorLog
from ..models.product import Product


class MerchantPredictionService:
    HISTORY_DAYS = 30
    RECENT_DAYS = 7

    def build_sales_forecast(self, merchant_id, days=30):
        days = int(days or 30)
        days = max(1, min(days, 90))

        top_product = self._select_top_product(merchant_id)
        if top_product is None:
            return self._build_fallback("暂无可预测商品：近7/30天购买数据不足")

        product_id, recent_purchase_count = top_product
        product_payload = self._serialize_product(merchant_id, product_id)

        history = self._build_history(merchant_id, product_id)
        forecast = self._build_forecast(history, days)
        forecast_values = [item["value"] for item in forecast]
        total = int(sum(forecast_values))
        confidence = self._estimate_confidence(history)
        margin = self._interval_margin(confidence)
        lower = max(0, int(round(total * (1 - margin))))
        upper = max(lower, int(round(total * (1 + margin))))

        avg_30 = sum(item["value"] for item in history) / max(len(history), 1)
        avg_7 = sum(item["value"] for item in history[-self.RECENT_DAYS :]) / self.RECENT_DAYS

        explain = [
            f"已选取近7天购买最多商品：{product_payload.get('name', '')}（近7天成交 {recent_purchase_count} 笔）。",
            f"过去30天日均销量 {avg_30:.2f}，近7天日均销量 {avg_7:.2f}。",
            f"预测采用近7天日均销量为基线，置信度 {confidence}，区间按 ±{int(margin * 100)}% 估计。",
        ]

        return {
            "product": product_payload,
            "history": history,
            "forecast": forecast,
            "forecast_total": {"value": total, "lower": lower, "upper": upper},
            "confidence": confidence,
            "explain": explain,
        }

    def _build_fallback(self, message):
        return {
            "product": None,
            "history": [],
            "forecast": [],
            "forecast_total": {"value": 0, "lower": 0, "upper": 0},
            "confidence": "low",
            "explain": [message],
        }

    def _select_top_product(self, merchant_id):
        threshold = datetime.utcnow() - timedelta(days=self.RECENT_DAYS)
        row = (
            db.session.query(BehaviorLog.product_id, func.count(BehaviorLog.id).label("cnt"))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= threshold,
            )
            .group_by(BehaviorLog.product_id)
            .order_by(func.count(BehaviorLog.id).desc(), BehaviorLog.product_id.asc())
            .first()
        )
        if row is not None:
            return int(row[0]), int(row[1])

        threshold = datetime.utcnow() - timedelta(days=self.HISTORY_DAYS)
        row = (
            db.session.query(BehaviorLog.product_id, func.count(BehaviorLog.id).label("cnt"))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= threshold,
            )
            .group_by(BehaviorLog.product_id)
            .order_by(func.count(BehaviorLog.id).desc(), BehaviorLog.product_id.asc())
            .first()
        )
        if row is None:
            return None
        return int(row[0]), int(row[1])

    def _serialize_product(self, merchant_id, product_id):
        product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
        if product is not None:
            return {
                "id": product.id,
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "brand": product.brand,
                "price": float(product.price or 0),
                "image_url": product.image_url,
            }

        last_log = (
            BehaviorLog.query.filter_by(merchant_id=merchant_id, product_id=product_id)
            .order_by(BehaviorLog.created_at.desc(), BehaviorLog.id.desc())
            .first()
        )
        if last_log is None:
            return {"id": product_id, "name": "", "category": "", "brand": "", "image_url": ""}

        return {
            "id": product_id,
            "product_id": product_id,
            "name": last_log.product_name,
            "category": last_log.category,
            "brand": last_log.brand or "",
            "price": float(last_log.price or 0),
            "image_url": "",
        }

    def _build_history(self, merchant_id, product_id):
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=self.HISTORY_DAYS - 1)
        start_dt = datetime.combine(start_date, datetime.min.time())
        date_expr = func.date(BehaviorLog.created_at)

        rows = (
            db.session.query(date_expr, func.count(BehaviorLog.id))
            .filter(
                BehaviorLog.merchant_id == merchant_id,
                BehaviorLog.product_id == product_id,
                BehaviorLog.action_type == "purchase",
                BehaviorLog.created_at >= start_dt,
            )
            .group_by(date_expr)
            .all()
        )
        value_map = {str(day): int(count) for day, count in rows}
        return [
            {"date": (start_date + timedelta(days=i)).isoformat(), "value": value_map.get((start_date + timedelta(days=i)).isoformat(), 0)}
            for i in range(self.HISTORY_DAYS)
        ]

    def _build_forecast(self, history, days):
        end_date = datetime.utcnow().date()
        recent_values = [item["value"] for item in history[-self.RECENT_DAYS :]]
        recent_avg = sum(recent_values) / self.RECENT_DAYS

        baseline = max(0.0, recent_avg)
        if baseline <= 0:
            baseline = sum(item["value"] for item in history) / max(len(history), 1)

        trend = 0.0
        if len(history) >= self.RECENT_DAYS * 2:
            prev_values = [item["value"] for item in history[-self.RECENT_DAYS * 2 : -self.RECENT_DAYS]]
            prev_avg = sum(prev_values) / self.RECENT_DAYS
            trend = (baseline - prev_avg) / max(prev_avg, 1.0)
            trend = max(-0.2, min(trend * 0.3, 0.3))

        items = []
        for offset in range(1, days + 1):
            factor = 1.0 + trend * (offset / max(days, 1))
            value = int(round(max(0.0, baseline * factor)))
            items.append({"date": (end_date + timedelta(days=offset)).isoformat(), "value": value})
        return items

    def _estimate_confidence(self, history):
        values = [item["value"] for item in history]
        total = sum(values)
        non_zero_days = sum(1 for value in values if value > 0)
        if total >= 30 and non_zero_days >= 10:
            return "high"
        if total >= 10 and non_zero_days >= 5:
            return "medium"
        return "low"

    def _interval_margin(self, confidence):
        if confidence == "high":
            return 0.15
        if confidence == "medium":
            return 0.25
        return 0.4
