def test_login_returns_token(client, seeded_user):
    response = client.post(
        "/api/auth/login",
        json={"username": "merchant_demo", "password": "demo123"},
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert "token" in payload
    assert payload["user"]["username"] == seeded_user.username
    assert payload["user"]["role"] == seeded_user.role


def test_me_requires_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(client, seeded_user):
    login_response = client.post(
        "/api/auth/login",
        json={"username": "merchant_demo", "password": "demo123"},
    )
    token = login_response.get_json()["token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["id"] == seeded_user.id
    assert response.get_json()["user"]["username"] == seeded_user.username
