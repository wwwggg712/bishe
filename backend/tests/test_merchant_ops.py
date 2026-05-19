from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.behavior_log import BehaviorLog
from app.models.product import Product
from app.models.user import User


def test_product_has_cost_price_column(seeded_demo_data):
    product = Product.query.first()
    assert hasattr(product, "cost_price")
    assert product.cost_price is not None
    assert Decimal(str(product.cost_price)) > 0


def _persist_purchase_logs(merchant_id, product, count):
    entities = []
    for idx in range(count):
        now = datetime.utcnow()
        entities.append(
            BehaviorLog(
                log_id=f"purchase-{merchant_id}-{product.id}-{idx}-{idx + 1000}",
                user_id=999,
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
                timestamp=now,
                created_at=now,
            )
        )
    db.session.add_all(entities)
    db.session.commit()
    return entities


def test_merchant_ops_overview_returns_profit_and_lists(
    client, merchant_headers, seeded_demo_data
):
    merchant = User.query.filter_by(username="merchant_demo").first()
    assert merchant is not None
    product = Product.query.filter_by(merchant_id=merchant.id).first()
    assert product is not None

    product.stock = 0
    db.session.commit()

    _persist_purchase_logs(merchant.id, product, 2)

    response = client.get(
        "/api/merchant/ops/overview?days=30&low_sales_threshold=3&brand_top_n=5",
        headers=merchant_headers,
    )
    assert response.status_code == 200

    payload = response.get_json()
    second = client.get(
        "/api/merchant/ops/overview?days=30&low_sales_threshold=3&brand_top_n=5",
        headers=merchant_headers,
    )
    assert second.status_code == 200
    payload_second = second.get_json()
    assert payload["summary"]["days"] == 30
    assert payload["summary"]["revenue"] > 0
    assert payload["summary"]["cost"] > 0
    assert "profit" in payload["summary"]
    assert "inventory_items" in payload
    assert "delist_suggestions" in payload
    assert "inactive_items" in payload
    assert "focus_brands" in payload
    assert payload["focus_brands"][0]["purchase_count_30d"] >= 2
    assert payload["focus_brands"][0]["top_product_name"]

    allowed_colors = {"红", "蓝", "黑", "白", "灰", "绿"}
    for section in ["inventory_items", "delist_suggestions", "inactive_items"]:
        for item in payload[section]:
            assert "color_breakdown" in item
            stock = int(item.get("stock") or 0)
            breakdown = item["color_breakdown"]
            if stock <= 0:
                assert breakdown == []
                continue
            assert sum(part["count"] for part in breakdown) == stock
            assert all(part["count"] > 0 for part in breakdown)
            assert all(part["color"] in allowed_colors for part in breakdown)

    first_delist = next(
        (item for item in payload["delist_suggestions"] if item["product_id"] == product.id),
        None,
    )
    assert first_delist is not None
    assert first_delist["stock"] == 0
    assert first_delist["color_breakdown"] == []
    second_delist = next(
        (item for item in payload_second["delist_suggestions"] if item["product_id"] == product.id),
        None,
    )
    assert second_delist is not None
    assert second_delist["color_breakdown"] == first_delist["color_breakdown"]

    first_item = None
    if payload["inventory_items"]:
        first_item = payload["inventory_items"][0]
    elif payload["inactive_items"]:
        first_item = payload["inactive_items"][0]
    assert first_item is not None
    assert "image_url" in first_item
    if payload["delist_suggestions"]:
        assert "image_url" in payload["delist_suggestions"][0]


def test_merchant_can_deactivate_product(client, merchant_headers, seeded_demo_data):
    merchant = User.query.filter_by(username="merchant_demo").first()
    assert merchant is not None
    product = Product.query.filter_by(merchant_id=merchant.id, is_active=True).first()
    assert product is not None

    response = client.post(
        f"/api/merchant/products/{product.id}/deactivate",
        headers=merchant_headers,
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product"]["id"] == product.id
    assert payload["product"]["is_active"] is False

    updated = db.session.get(Product, product.id)
    assert updated.is_active is False
