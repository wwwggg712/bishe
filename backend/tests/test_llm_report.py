def test_llm_report_returns_fallback_summary_without_external_llm(client, merchant_headers):
    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={
            "product_name": "轻量跑鞋",
            "hot_score": 128,
            "trend_label": "up",
            "purchase_rate": 0.07,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "summary" in payload
    assert "轻量跑鞋" in payload["summary"]
    assert "128" in payload["summary"]
    assert "up" in payload["summary"]
    assert "7.00%" in payload["summary"]


def test_llm_report_supports_merchant_scene(client, merchant_headers):
    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={
            "scene": "merchant",
            "product_name": "轻量跑鞋",
            "hot_score": 186,
            "trend_label": "warning",
            "purchase_rate": 0.083,
            "anomaly_count": 2,
            "cold_product_count": 1,
            "category_name": "运动鞋",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "summary" in payload
    assert "经营" in payload["summary"]
    assert "轻量跑鞋" in payload["summary"]


def test_llm_report_supports_customer_scene(client, customer_headers):
    response = client.post(
        "/api/llm/report",
        headers=customer_headers,
        json={
            "scene": "customer",
            "product_name": "轻量跑鞋",
            "trend_product_name": "城市双肩包",
            "preferred_category": "运动鞋服",
            "price_band": "中高消费偏好",
            "active_hour": "20点",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "summary" in payload
    assert "推荐" in payload["summary"]
    assert "运动鞋服" in payload["summary"]


def test_llm_report_returns_provider_mode_when_external_model_is_available(
    client, merchant_headers, monkeypatch
):
    from app.routes.llm import llm_service

    monkeypatch.setattr(
        llm_service,
        "_provider_config",
        lambda: {
            "provider": "openai-compatible",
            "model": "deepseek-chat",
            "api_key": "demo-key",
            "base_url": "https://example.com/v1/chat/completions",
        },
    )
    monkeypatch.setattr(
        llm_service,
        "_call_provider",
        lambda payload, config: {
            "summary": "这是外部模型返回的经营分析。",
            "mode": "provider",
            "provider": config["provider"],
            "model": config["model"],
        },
    )

    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={"scene": "merchant", "product_name": "轻量跑鞋"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "provider"
    assert payload["provider"] == "openai-compatible"
    assert payload["model"] == "deepseek-chat"


def test_llm_report_returns_fallback_mode_when_provider_config_is_missing(
    client, merchant_headers, monkeypatch
):
    from app.routes.llm import llm_service

    monkeypatch.setattr(llm_service, "_provider_config", lambda: None)

    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={"scene": "merchant", "product_name": "轻量跑鞋"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "fallback"
    assert payload["provider"] == "internal"
    assert payload["model"] == "rule-based-fallback"


def test_llm_report_falls_back_when_provider_call_raises(
    client, merchant_headers, monkeypatch
):
    from app.routes.llm import llm_service

    monkeypatch.setattr(
        llm_service,
        "_provider_config",
        lambda: {
            "provider": "openai-compatible",
            "model": "deepseek-chat",
            "api_key": "demo-key",
            "base_url": "https://example.com/v1/chat/completions",
        },
    )

    def raise_error(payload, config):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm_service, "_call_provider", raise_error)

    response = client.post(
        "/api/llm/report",
        headers=merchant_headers,
        json={"scene": "merchant", "product_name": "轻量跑鞋"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "error"
    assert payload["provider"] == "openai-compatible"
    assert payload["model"] == "deepseek-chat"
    assert payload["base_url"] == "https://example.com/v1/chat/completions"
    assert "provider unavailable" in payload["error_message"]
    assert "轻量跑鞋" in payload["summary"]
