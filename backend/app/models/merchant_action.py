from datetime import datetime

from ..extensions import db


class MerchantAction(db.Model):
    __tablename__ = "merchant_actions"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    merchant = db.relationship("User", backref=db.backref("merchant_actions", lazy="select"))
    product = db.relationship("Product", backref=db.backref("merchant_actions", lazy="select"))

    def to_dict(self):
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "",
            "action_type": self.action_type,
            "created_at": self.created_at.isoformat(),
            "status": "recorded",
        }
