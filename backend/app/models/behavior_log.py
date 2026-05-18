from datetime import datetime

from ..extensions import db


class BehaviorLog(db.Model):
    __tablename__ = "behavior_logs"

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    merchant_id = db.Column(db.Integer, nullable=False, index=True)
    product_id = db.Column(db.Integer, nullable=False, index=True)
    product_name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    brand = db.Column(db.String(64), nullable=True)
    price = db.Column(db.Float, nullable=False)
    action_type = db.Column(db.String(32), nullable=False, index=True)
    region = db.Column(db.String(32), nullable=True, index=True)
    device_type = db.Column(db.String(32), nullable=True)
    source_channel = db.Column(db.String(32), nullable=False, index=True)
    session_id = db.Column(db.String(64), nullable=True)
    stay_duration = db.Column(db.Integer, nullable=True)
    is_new_user = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "log_id": self.log_id,
            "user_id": self.user_id,
            "merchant_id": self.merchant_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "brand": self.brand,
            "price": float(self.price),
            "action_type": self.action_type,
            "region": self.region,
            "device_type": self.device_type,
            "source_channel": self.source_channel,
            "session_id": self.session_id,
            "stay_duration": self.stay_duration,
            "is_new_user": self.is_new_user,
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
        }
