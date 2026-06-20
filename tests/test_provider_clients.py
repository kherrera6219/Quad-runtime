from __future__ import annotations

import json

import pytest

from quad.errors import QuadModelError
from quad.llm_client import (
    AnthropicMessagesClient,
    GeminiClient,
    OpenAIResponsesClient,
    client_from_name,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def _capture_urlopen(monkeypatch, payload):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(payload)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    return captured


def test_openai_responses_client_uses_responses_api(monkeypatch):
    captured = _capture_urlopen(monkeypatch, {"output_text": "OpenAI answer"})
    client = OpenAIResponsesClient(api_key="test-key", model_name="gpt-test", max_output_tokens=100)

    result = client.generate("system", "user", {"developer_prompt": "developer"})

    assert result.answer == "OpenAI answer"
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["payload"]["model"] == "gpt-test"
    assert captured["payload"]["instructions"] == "system\n\ndeveloper"
    assert captured["payload"]["input"] == "user"
    assert captured["payload"]["max_output_tokens"] == 100
    assert captured["headers"]["Authorization"] == "Bearer test-key"


def test_anthropic_messages_client_uses_messages_api(monkeypatch):
    captured = _capture_urlopen(
        monkeypatch,
        {"content": [{"type": "text", "text": "Claude answer"}]},
    )
    client = AnthropicMessagesClient(api_key="test-key", model_name="claude-test", max_tokens=100)

    result = client.generate("system", "user", {"developer_prompt": "developer"})

    assert result.answer == "Claude answer"
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["payload"]["model"] == "claude-test"
    assert captured["payload"]["max_tokens"] == 100
    assert captured["payload"]["system"] == "system\n\ndeveloper"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "user"}]
    assert captured["headers"]["X-api-key"] == "test-key"
    assert captured["headers"]["Anthropic-version"] == "2023-06-01"


def test_gemini_client_uses_generate_content_api(monkeypatch):
    captured = _capture_urlopen(
        monkeypatch,
        {"candidates": [{"content": {"parts": [{"text": "Gemini answer"}]}}]},
    )
    client = GeminiClient(api_key="test-key", model_name="gemini-test", max_output_tokens=100)

    result = client.generate("system", "user", {"developer_prompt": "developer"})

    assert result.answer == "Gemini answer"
    assert captured["url"] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent?key=test-key"
    assert captured["payload"]["systemInstruction"]["parts"] == [{"text": "system\n\ndeveloper"}]
    assert captured["payload"]["contents"] == [{"role": "user", "parts": [{"text": "user"}]}]
    assert captured["payload"]["generationConfig"] == {"maxOutputTokens": 100}


@pytest.mark.parametrize(
    ("provider", "client_type"),
    [
        ("openai", OpenAIResponsesClient),
        ("anthropic", AnthropicMessagesClient),
        ("claude", AnthropicMessagesClient),
        ("gemini", GeminiClient),
    ],
)
def test_client_from_name_resolves_frontier_providers(provider, client_type):
    assert isinstance(client_from_name(provider, provider_model="test-model"), client_type)


@pytest.mark.parametrize(
    "client",
    [
        OpenAIResponsesClient(api_key="", model_name="gpt-test"),
        AnthropicMessagesClient(api_key="", model_name="claude-test"),
        GeminiClient(api_key="", model_name="gemini-test"),
    ],
)
def test_frontier_clients_require_api_keys(client):
    with pytest.raises(QuadModelError):
        client.generate("system", "user", {})
