def test_price_compare_returns_platform_offers(client, customer_headers, seeded_demo_data):
    response = client.get("/api/price-compare?product_id=1", headers=customer_headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product"]["product_id"] == 1
    platforms = [item["platform"] for item in payload["offers"]]
    assert platforms == ["抖音", "京东", "拼多多", "得物"]
    assert payload["best"]["platform"]
    assert payload["best"]["saving"] >= 0


def test_price_compare_is_deterministic(client, customer_headers, seeded_demo_data):
    response1 = client.get("/api/price-compare?product_id=1", headers=customer_headers)
    response2 = client.get("/api/price-compare?product_id=1", headers=customer_headers)
    assert response1.get_json()["offers"] == response2.get_json()["offers"]

