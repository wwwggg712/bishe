def test_merchant_can_record_operational_action(client, merchant_headers, seeded_demo_data):
    response = client.post(
        "/api/strategy/actions",
        headers=merchant_headers,
        json={
            "product_id": 1,
            "action_type": "focus_watch",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["action"]["product_id"] == 1
    assert payload["action"]["action_type"] == "focus_watch"
    assert payload["summary"]["total"] >= 1


def test_merchant_action_summary_returns_counts(client, merchant_headers, seeded_demo_data):
    client.post(
        "/api/strategy/actions",
        headers=merchant_headers,
        json={
            "product_id": 1,
            "action_type": "promote",
        },
    )

    response = client.get("/api/strategy/actions/summary", headers=merchant_headers)
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["summary"]["total"] >= 1
    assert "promote" in payload["summary"]["by_action"]


def test_non_merchant_cannot_record_operational_action(client, customer_headers, seeded_demo_data):
    response = client.post(
        "/api/strategy/actions",
        headers=customer_headers,
        json={
            "product_id": 1,
            "action_type": "focus_watch",
        },
    )

    assert response.status_code == 403
