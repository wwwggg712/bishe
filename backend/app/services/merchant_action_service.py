from collections import Counter
from datetime import datetime

from ..extensions import db
from ..models.merchant_action import MerchantAction
from ..models.product import Product


class MerchantActionService:
    VALID_ACTION_TYPES = {
        "focus_watch",
        "promote",
        "restock_priority",
        "optimize_detail",
    }

    ACTION_LABELS = {
        "focus_watch": "设为重点观察",
        "promote": "加入促销",
        "restock_priority": "补货优先",
        "optimize_detail": "优化详情页",
    }

    def record_action(self, merchant_id, product_id, action_type):
        if action_type not in self.VALID_ACTION_TYPES:
            raise ValueError("不支持的运营动作")

        product = Product.query.filter_by(id=product_id, merchant_id=merchant_id).first()
        if product is None:
            raise LookupError("未找到可操作的商品")

        action = MerchantAction(
            merchant_id=merchant_id,
            product_id=product.id,
            action_type=action_type,
        )
        db.session.add(action)
        db.session.commit()

        return {
            "action": self._serialize_action(action),
            "summary": self.build_summary(merchant_id)["summary"],
        }

    def build_summary(self, merchant_id):
        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        actions = (
            MerchantAction.query.filter(
                MerchantAction.merchant_id == merchant_id,
                MerchantAction.created_at >= start_of_day,
            )
            .order_by(MerchantAction.created_at.desc(), MerchantAction.id.desc())
            .all()
        )
        counter = Counter(action.action_type for action in actions)

        return {
            "summary": {
                "total": len(actions),
                "by_action": dict(counter),
            },
            "items": [self._serialize_action(action) for action in actions],
        }

    def _serialize_action(self, action):
        payload = action.to_dict()
        payload["action_label"] = self.ACTION_LABELS.get(action.action_type, action.action_type)
        return payload
