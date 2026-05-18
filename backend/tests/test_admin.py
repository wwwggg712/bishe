from app.models.user import User
from app.models.behavior_log import BehaviorLog
from app.extensions import db


def test_admin_users_returns_all_users(client, admin_headers):
    response = client.get("/api/admin/users", headers=admin_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["users"]
    assert any(user["role"] == "admin" for user in payload["users"])
    assert any(user["role"] == "merchant" for user in payload["users"])
    assert any(user["role"] == "customer" for user in payload["users"])
    assert payload["total"] == User.query.count()


def test_non_admin_cannot_access_admin_users(client, customer_headers):
    response = client.get("/api/admin/users", headers=customer_headers)
    assert response.status_code == 403


def test_admin_log_preview_returns_recent_logs_and_summary(client, admin_headers, seeded_demo_data):
    generate_response = client.post("/api/simulation/generate-once", headers=admin_headers)
    assert generate_response.status_code == 200

    response = client.get("/api/admin/logs/preview", headers=admin_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["total_logs"] >= 1
    assert payload["summary"]["action_type_count"] >= 1
    assert payload["summary"]["latest_timestamp"]
    assert "sample_generated_count" in payload["summary"]
    assert payload["generation_note"]
    assert payload["recent_logs"]


def test_admin_algorithm_pipeline_returns_live_processing_summary(
    client, admin_headers, seeded_demo_data, persist_behavior_logs
):
    persist_behavior_logs(
        [
        {
            "log_id": "log-1",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "view",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "search",
            "session_id": "s-1",
            "stay_duration": 30,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:00:00",
        },
        {
            "log_id": "log-2",
            "user_id": 3,
            "merchant_id": 2,
            "product_id": 1,
            "product_name": "轻量跑鞋",
            "category": "运动鞋",
            "brand": "CloudStep",
            "price": 299.0,
            "action_type": "purchase",
            "region": "华东",
            "device_type": "mobile",
            "source_channel": "customer_page",
            "session_id": "s-2",
            "stay_duration": 45,
            "is_new_user": False,
            "timestamp": "2026-05-13T10:05:00",
        },
        ]
    )

    response = client.get("/api/admin/algorithm-pipeline", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert set(payload.keys()) == {
        "log_input",
        "aggregation",
        "scoring",
        "portrait_and_recommendation",
        "anomalies",
        "segmentation",
        "ai_meta",
    }
    assert payload["log_input"]["total_logs"] == 2
    assert payload["aggregation"]["behavior_count"] == 2
    assert payload["aggregation"]["view_count"] == 1
    assert payload["aggregation"]["purchase_count"] == 1
    assert payload["scoring"]["weight_rule"] == "view=1, click=2, favorite=3, cart=5, purchase=8"
    assert payload["portrait_and_recommendation"]["real_action_logs"] == 1
    assert payload["ai_meta"]["mode"] in {"provider", "fallback"}


def test_behavior_log_table_is_created(app):
    with app.app_context():
        inspector = db.inspect(db.engine)
        assert "behavior_logs" in inspector.get_table_names()


def test_simulation_bulk_persists_behavior_logs(client, admin_headers):
    response = client.post("/api/simulation/generate-bulk", headers=admin_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["generated_count"] == 2000
    assert BehaviorLog.query.count() == 2000


def test_admin_log_preview_supports_pagination(client, admin_headers):
    client.post("/api/simulation/generate-bulk", headers=admin_headers)

    response = client.get(
        "/api/admin/logs/preview?page=1&page_size=50",
        headers=admin_headers,
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["pagination"]["page"] == 1
    assert payload["pagination"]["page_size"] == 50
    assert payload["pagination"]["total"] == 2000
    assert payload["summary"]["sample_generated_count"] == 50
    assert len(payload["recent_logs"]) == 50


def test_admin_log_metrics_returns_summary_and_breakdowns(
    client, admin_headers, seeded_demo_data
):
    client.post("/api/simulation/generate-once", headers=admin_headers)

    response = client.get("/api/admin/logs/metrics", headers=admin_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["total_logs"] >= 1
    assert payload["summary"]["latest_timestamp"]
    assert "last_minute_added" in payload["summary"]
    assert payload["action_breakdown"]
    assert "brand_breakdown" in payload


def test_admin_can_cleanup_logs_keep_last(client, admin_headers):
    client.post("/api/simulation/generate-bulk", headers=admin_headers)
    assert BehaviorLog.query.count() == 2000

    response = client.post(
        "/api/admin/logs/cleanup",
        headers=admin_headers,
        json={"keep_last": 500},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["kept_count"] == 500
    assert payload["deleted_count"] == 1500
    assert BehaviorLog.query.count() == 500
