from app.models.product import Product
from app.models.task import Task
from app.models.user import User
from app.utils.log_schema import DEVICE_TYPES, LOG_ACTIONS, LOG_FIELD_NAMES, SOURCE_CHANNELS
from app.utils.seed_data import seed_demo_data


def test_seed_demo_data_creates_demo_entities(app):
    with app.app_context():
        seed_demo_data()

        usernames = {user.username for user in User.query.all()}

        assert {"admin_demo", "merchant_demo", "customer_demo"} <= usernames
        assert Product.query.count() >= 4
        assert Task.query.filter_by(task_type="simulation").count() == 1


def test_seed_demo_data_creates_richer_catalog(app):
    with app.app_context():
        seed_demo_data()
        products = Product.query.all()
        categories = {product.category for product in products}

        assert len(products) >= 24
        assert len(categories) >= 8


def test_generate_once_returns_logs(client, auth_headers, seeded_demo_data):
    response = client.post("/api/simulation/generate-once", headers=auth_headers)

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["generated_count"] > 0
    assert isinstance(payload["preview"], list)
    assert payload["preview"]

    preview_log = payload["preview"][0]

    assert set(LOG_FIELD_NAMES).issubset(preview_log)
    assert preview_log["action_type"] in LOG_ACTIONS
    assert preview_log["device_type"] in DEVICE_TYPES
    assert preview_log["source_channel"] in SOURCE_CHANNELS


def test_simulation_start_stop_and_tasks(client, auth_headers, seeded_demo_data):
    start_response = client.post("/api/simulation/start", headers=auth_headers)
    assert start_response.status_code == 200

    start_payload = start_response.get_json()
    assert start_payload["task"]["status"] == "running"
    assert start_payload["generated_count"] > 0

    tasks_response = client.get("/api/simulation/tasks", headers=auth_headers)
    assert tasks_response.status_code == 200
    tasks_payload = tasks_response.get_json()
    assert tasks_payload["tasks"]
    assert any(task["status"] == "running" for task in tasks_payload["tasks"])

    stop_response = client.post("/api/simulation/stop", headers=auth_headers)
    assert stop_response.status_code == 200
    stop_payload = stop_response.get_json()
    assert stop_payload["task"]["status"] == "stopped"


def test_generate_bulk_returns_2000_logs(client, admin_headers, seeded_demo_data):
    response = client.post("/api/simulation/generate-bulk", headers=admin_headers)

    assert response.status_code == 200

    payload = response.get_json()
    assert payload["generated_count"] == 2000
    assert isinstance(payload["preview"], list)


def test_generate_once_from_db_only_creates_customer_behavior_logs(
    client, admin_headers, seeded_demo_data
):
    from app.models.user import User
    from app.services.simulation_service import SimulationService

    logs = SimulationService().generate_once_from_db(batch_size=20)
    customer_ids = {user.id for user in User.query.filter_by(role="customer").all()}

    assert logs
    assert all(log["user_id"] in customer_ids for log in logs)
