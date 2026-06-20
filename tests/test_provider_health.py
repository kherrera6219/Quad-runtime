from __future__ import annotations

from quad.llm_client import AnthropicMessagesClient, EchoLLMClient, GeminiClient, OllamaClient, OpenAIResponsesClient
from quad.runtime import QuadRuntime


def test_echo_provider_health_is_configured():
    health = QuadRuntime(llm_client=EchoLLMClient()).check_provider()

    assert health.provider == "echo"
    assert health.configured is True
    assert health.issues == []


def test_openai_provider_health_reports_missing_api_key():
    health = OpenAIResponsesClient(api_key="", model_name="gpt-test").validate_configuration()

    assert health.provider == "openai"
    assert health.configured is False
    assert "OPENAI_API_KEY is required." in health.issues


def test_anthropic_provider_health_reports_invalid_values():
    health = AnthropicMessagesClient(
        api_key="key",
        model_name=" ",
        base_url="not-a-url",
        timeout_seconds=0,
        max_retries=-1,
        max_tokens=0,
        anthropic_version="",
    ).validate_configuration()

    assert health.configured is False
    assert "model_name must be non-empty." in health.issues
    assert "base_url must start with http:// or https://." in health.issues
    assert "timeout_seconds must be greater than 0." in health.issues
    assert "max_retries must be 0 or greater." in health.issues
    assert "max_tokens must be greater than 0." in health.issues
    assert "anthropic_version must be non-empty." in health.issues


def test_gemini_provider_health_accepts_google_api_key():
    health = GeminiClient(api_key="key", model_name="gemini-test").validate_configuration()

    assert health.provider == "gemini"
    assert health.configured is True


def test_ollama_provider_health_validates_common_fields():
    health = OllamaClient(model_name="", base_url="localhost", timeout_seconds=-1, max_retries=-1).validate_configuration()

    assert health.configured is False
    assert len(health.issues) == 4
