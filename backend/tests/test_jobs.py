from datetime import datetime

from app.models.task import Task


def _make_log(*, log_id, user_id, product_id, product_name, action_type):
    return {
        "log_id": log_id,
        "user_id": user_id,
        "merchant_id": 2,
        "product_id": product_id,
        "product_name": product_name,
        "category": "运动鞋",
        "brand": "Demo Brand",
        "price": 199.0,
        "action_type": action_type,
        "region": "华东",
        "device_type": "mobile",
        "source_channel": "homepage",
        "session_id": f"session-{user_id}",
        "stay_duration": 30,
        "is_new_user": False,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _build_auth_headers(client, username, password="demo123"):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_daily_job_persists_metrics(app, persist_behavior_logs):
    from app.models.daily_metric import DailyProductMetric
    from app.tasks.jobs import run_daily_aggregation

    persist_behavior_logs(
        [
        _make_log(
            log_id="log-1",
            user_id=3,
            product_id=1,
            product_name="轻量跑鞋",
            action_type="view",
        ),
        _make_log(
            log_id="log-2",
            user_id=3,
            product_id=1,
            product_name="轻量跑鞋",
            action_type="purchase",
        ),
        _make_log(
            log_id="log-3",
            user_id=4,
            product_id=2,
            product_name="透气训练T恤",
            action_type="click",
        ),
        ]
    )

    with app.app_context():
        result = run_daily_aggregation()

        assert result["status"] == "ok"
        assert result["saved_metrics"] == 2

        metrics = DailyProductMetric.query.order_by(
            DailyProductMetric.product_id.asc()
        ).all()
        assert len(metrics) == 2
        assert metrics[0].product_name == "轻量跑鞋"
        assert metrics[0].view_count == 1
        assert metrics[0].purchase_count == 1
        assert metrics[0].hot_score == 9


def test_admin_jobs_returns_registered_jobs(client, seeded_demo_data):
    headers = _build_auth_headers(client, "admin_demo")

    response = client.get("/api/admin/jobs", headers=headers)

    assert response.status_code == 200

    payload = response.get_json()

    assert "jobs" in payload
    assert any(job["name"] == "scheduled_simulation" for job in payload["jobs"])
    assert any(job["name"] == "daily_aggregation" for job in payload["jobs"])


def test_admin_can_run_daily_aggregation_job(
    client, app, seeded_demo_data, persist_behavior_logs
):
    headers = _build_auth_headers(client, "admin_demo")
    persist_behavior_logs(
        [
        _make_log(
            log_id="log-4",
            user_id=3,
            product_id=1,
            product_name="轻量跑鞋",
            action_type="view",
        ),
        _make_log(
            log_id="log-5",
            user_id=3,
            product_id=1,
            product_name="轻量跑鞋",
            action_type="cart",
        ),
        ]
    )

    response = client.post(
        "/api/admin/jobs/run",
        headers=headers,
        json={"job_name": "daily_aggregation"},
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["result"]["status"] == "ok"

    with app.app_context():
        task = Task.query.filter_by(name="daily_aggregation").first()
        assert task is not None
        assert task.status == "success"
        assert task.last_run_at is not None


def test_non_admin_cannot_run_jobs(client, seeded_demo_data):
    headers = _build_auth_headers(client, "merchant_demo")

    response = client.post(
        "/api/admin/jobs/run",
        headers=headers,
        json={"job_name": "daily_aggregation"},
    )

    assert response.status_code == 403
