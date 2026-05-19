def test_recommendations_include_price_and_image_url(
    client, customer_headers, seeded_demo_data
):
    response = client.get("/api/recommendations/me", headers=customer_headers)
    assert response.status_code == 200
    payload = response.get_json()
    if not payload["items"]:
        return
    item = payload["items"][0]
    assert "price" in item
    assert "brand" in item
    assert "image_url" in item

