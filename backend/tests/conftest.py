import pytest

from app import create_app
from app.extensions import db
from app.models.behavior_log import BehaviorLog
from app.models.user import User
from app.utils.seed_data import seed_demo_data


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seeded_user(app):
    user = User(
        username="merchant_demo",
        role="merchant",
        nickname="Merchant Demo",
        region="华东",
    )
    user.set_password("demo123")

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture()
def seeded_demo_data(app):
    with app.app_context():
        return seed_demo_data()


@pytest.fixture()
def auth_headers(client, seeded_demo_data):
    response = client.post(
        "/api/auth/login",
        json={"username": "merchant_demo", "password": "demo123"},
    )
    assert response.status_code == 200
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def merchant_headers(auth_headers):
    return auth_headers


@pytest.fixture()
def admin_headers(client, seeded_demo_data):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin_demo", "password": "demo123"},
    )
    assert response.status_code == 200
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def customer_headers(client, seeded_demo_data):
    response = client.post(
        "/api/auth/login",
        json={"username": "customer_demo", "password": "demo123"},
    )
    assert response.status_code == 200
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def persist_behavior_logs(app):
    from datetime import datetime

    def _persist(logs):
        entities = []
        for log in logs:
            ts = log.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            if ts is None:
                ts = datetime.utcnow()

            entities.append(
                BehaviorLog(
                    log_id=log["log_id"],
                    user_id=log["user_id"],
                    merchant_id=log["merchant_id"],
                    product_id=log["product_id"],
                    product_name=log["product_name"],
                    category=log["category"],
                    brand=log.get("brand"),
                    price=float(log.get("price", 0)),
                    action_type=log["action_type"],
                    region=log.get("region"),
                    device_type=log.get("device_type"),
                    source_channel=log.get("source_channel") or "unknown",
                    session_id=log.get("session_id"),
                    stay_duration=log.get("stay_duration"),
                    is_new_user=bool(log.get("is_new_user", False)),
                    timestamp=ts,
                )
            )
        db.session.add_all(entities)
        db.session.commit()
        return entities

    return _persist
