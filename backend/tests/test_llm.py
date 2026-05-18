from urllib import error as urllib_error


def test_llm_report_returns_error_mode_when_provider_fails(client, admin_headers, monkeypatch):
    from app.services import llm_service as llm_module

    def _raise(*args, **kwargs):
        raise urllib_error.URLError("boom")

    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setattr(llm_module.urllib_request, "urlopen", _raise)

    response = client.post(
        "/api/llm/report",
        headers=admin_headers,
        json={"scene": "merchant"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["mode"] == "error"
    assert payload["provider"] == "deepseek"
    assert payload["model"] == "deepseek-chat"
    assert payload["base_url"]
    assert payload["error_message"]

