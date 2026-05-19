from datetime import datetime, timedelta

from app.extensions import db
from app.models.behavior_log import BehaviorLog
from app.models.product import Product
from app.models.user import User


def _create_purchase_log(merchant_id, product, created_at, idx):
    return BehaviorLog(
        log_id=f"forecast-purchase-{merchant_id}-{product.id}-{idx}-{int(created_at.timestamp())}",
        user_id=1000 + idx,
        merchant_id=merchant_id,
        product_id=product.id,
        product_name=product.name,
        category=product.category,
        brand=product.brand,
        price=float(product.price),
        action_type="purchase",
        region="华东",
        device_type="ios",
        source_channel="customer_page",
        session_id="sess",
        stay_duration=10,
        is_new_user=False,
        timestamp=created_at,
        created_at=created_at,
    )


def test_sales_forecast_returns_fallback_when_no_data(client, merchant_headers, seeded_demo_data):
    response = client.get(
        "/api/merchant/prediction/sales-forecast?days=30",
        headers=merchant_headers,
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product"] is None
    assert payload["history"] == []
    assert payload["forecast"] == []
    assert payload["forecast_total"] == {"value": 0, "lower": 0, "upper": 0}
    assert payload["confidence"] == "low"
    assert isinstance(payload["explain"], list)
    assert payload["explain"]


def test_sales_forecast_selects_top_product_and_returns_series(
    client, merchant_headers, seeded_demo_data
):
    merchant = User.query.filter_by(username="merchant_demo").first()
    assert merchant is not None
    products = Product.query.filter_by(merchant_id=merchant.id).order_by(Product.id.asc()).limit(2).all()
    assert len(products) == 2
    product_a, product_b = products

    today = datetime.utcnow().date()
    day_1 = datetime.combine(today - timedelta(days=1), datetime.min.time())
    day_2 = datetime.combine(today - timedelta(days=2), datetime.min.time())

    logs = []
    for idx in range(4):
        logs.append(_create_purchase_log(merchant.id, product_b, day_1 + timedelta(minutes=idx), idx))
    logs.append(_create_purchase_log(merchant.id, product_b, day_2, 20))
    for idx in range(3):
        logs.append(_create_purchase_log(merchant.id, product_a, day_1 + timedelta(minutes=30 + idx), 40 + idx))
    db.session.add_all(logs)
    db.session.commit()

    response = client.get(
        "/api/merchant/prediction/sales-forecast?days=30",
        headers=merchant_headers,
    )
    assert response.status_code == 200
    payload = response.get_json()

    assert payload["product"]["id"] == product_b.id
    assert payload["product"]["name"] == product_b.name
    assert len(payload["history"]) == 30
    assert len(payload["forecast"]) == 30

    history_map = {item["date"]: item["value"] for item in payload["history"]}
    assert history_map[(today - timedelta(days=1)).isoformat()] == 4
    assert history_map[(today - timedelta(days=2)).isoformat()] == 1

    forecast_total = payload["forecast_total"]
    assert forecast_total["lower"] <= forecast_total["value"] <= forecast_total["upper"]
    assert isinstance(payload["explain"], list)
    assert payload["explain"]
