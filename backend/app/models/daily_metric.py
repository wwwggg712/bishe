from datetime import date, datetime

from ..extensions import db


class DailyProductMetric(db.Model):
    __tablename__ = "daily_product_metrics"
    __table_args__ = (
        db.UniqueConstraint("product_id", "metric_date", name="uq_daily_product_metric"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False, index=True)
    product_name = db.Column(db.String(100), nullable=False)
    metric_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    click_count = db.Column(db.Integer, nullable=False, default=0)
    favorite_count = db.Column(db.Integer, nullable=False, default=0)
    cart_count = db.Column(db.Integer, nullable=False, default=0)
    purchase_count = db.Column(db.Integer, nullable=False, default=0)
    conversion_rate = db.Column(db.Float, nullable=False, default=0.0)
    hot_score = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
