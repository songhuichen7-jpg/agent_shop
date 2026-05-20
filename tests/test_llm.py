from src.llm import DeepSeekClient, parse_json_text


def test_parse_json_text_plain():
    assert parse_json_text('{"ok": true}') == {"ok": True}


def test_parse_json_text_fenced_json():
    assert parse_json_text('```json\n{"ok": true}\n```') == {"ok": True}


def test_mimo_provider_uses_fast_defaults(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("ONLINE_LLM_PROVIDER", "mimo")
    monkeypatch.setenv("MIMO_API_KEY", "test-key")

    client = DeepSeekClient()
    body = client._body("ping")

    assert client.provider == "mimo"
    assert client.base_url == "https://api.xiaomimimo.com/v1"
    assert body["model"] == "mimo-v2-flash"
    assert body["temperature"] == 0.3
    assert body["top_p"] == 0.95
    assert body["max_completion_tokens"] == 2048
    assert body["thinking"] == {"type": "disabled"}
    assert "reasoning_effort" not in body


def test_deepseek_provider_keeps_reasoning_defaults(monkeypatch):
    monkeypatch.setenv("ONLINE_LLM_PROVIDER", "deepseek")
    monkeypatch.delenv("ONLINE_LLM_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    client = DeepSeekClient()
    body = client._body("ping")

    assert client.provider == "deepseek"
    assert body["model"] == "deepseek-v4-pro"
    assert body["reasoning_effort"] == "high"
    assert body["thinking"] == {"type": "enabled"}
    assert "temperature" not in body


def test_deepseek_provider_uses_online_model_when_set(monkeypatch):
    monkeypatch.setenv("ONLINE_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("ONLINE_LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    client = DeepSeekClient()

    assert client.provider == "deepseek"
    assert client.model == "deepseek-v4-flash"
