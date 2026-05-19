from datetime import datetime

from app.extensions import db
from app.models.behavior_log import BehaviorLog


def _persist_log(merchant_id, product_id, product_name, category, brand, action_type):
    now = datetime.utcnow()
    entity = BehaviorLog(
        log_id=f"chart-{merchant_id}-{product_id}-{action_type}-{now.timestamp()}",
        user_id=123,
        merchant_id=merchant_id,
        product_id=product_id,
        product_name=product_name,
        category=category,
        brand=brand,
        price=99.0,
        action_type=action_type,
        region="华东",
        device_type="ios",
        source_channel="customer_page",
        session_id="sess",
        stay_duration=10,
        is_new_user=False,
        timestamp=now,
        created_at=now,
    )
    db.session.add(entity)
    db.session.commit()


def test_merchant_charts_share(client, merchant_headers, seeded_demo_data):
    _persist_log(2, 1, "轻量跑鞋", "运动鞋", "CloudStep", "view")
    _persist_log(2, 1, "轻量跑鞋", "运动鞋", "CloudStep", "purchase")
    response = client.get("/api/merchant/charts/share?top_n=5", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert "category_share" in payload
    assert "brand_share" in payload
    assert payload["category_share"]
    assert payload["brand_share"]


def test_merchant_charts_trend(client, merchant_headers, seeded_demo_data):
    _persist_log(2, 1, "轻量跑鞋", "运动鞋", "CloudStep", "view")
    response = client.get("/api/merchant/charts/trend?days=7", headers=merchant_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["days"]) == 7
    assert len(payload["series"]) == 2

