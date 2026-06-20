from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from quad.errors import QuadModelError
from quad.models import GenerationResult

DEFAULT_OPENAI_MODEL = "gpt-5.1"
DEFAULT_ANTHROPIC_MODEL = "claude-fable-5"
DEFAULT_GEMINI_MODEL = "gemini-3.5-pro"


class LLMClient(Protocol):
    model_name: str

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        ...


class EchoLLMClient:
    """Deterministic local client for smoke tests and offline demos."""

    model_name = "echo"

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        mode = metadata.get("mode", "normal")
        profile = metadata.get("output_profile", "quick")
        answer = (
            f"Mode: {mode.upper()}\n"
            f"Profile: {profile}\n\n"
            "This is a deterministic QUAD runtime smoke-test response. "
            "Replace `--model echo` with `--model ollama` for a real local model call."
        )
        return GenerationResult(answer=answer, model=self.model_name, raw={"echo": True})


class OllamaClient:
    def __init__(
        self,
        model_name: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 120,
        max_retries: int = 1,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        prompt = f"System:\n{system_prompt}\n\nDeveloper:\n{metadata.get('developer_prompt', '')}\n\nUser:\n{user_prompt}"
        payload = json.dumps({"model": self.model_name, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        raw: dict[str, Any] | None = None
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                break
            except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise QuadModelError(
                        f"Ollama request failed at {self.base_url} after {attempt + 1} attempt(s): {exc}"
                    ) from exc

        if raw is None:
            raise QuadModelError(f"Ollama request failed at {self.base_url}: no response body.")

        answer = raw.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise QuadModelError(f"Ollama returned an empty response for model `{self.model_name}`.")
        return GenerationResult(answer=answer, model=self.model_name, raw=raw)


class OpenAIResponsesClient:
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 120,
        max_retries: int = 1,
        max_output_tokens: int | None = None,
    ) -> None:
        self.model_name = model_name or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        if not self.api_key:
            raise QuadModelError("OPENAI_API_KEY is required for the OpenAI provider.")

        payload: dict[str, Any] = {
            "model": self.model_name,
            "instructions": _join_instructions(system_prompt, metadata.get("developer_prompt", "")),
            "input": user_prompt,
        }
        if self.max_output_tokens is not None:
            payload["max_output_tokens"] = self.max_output_tokens

        raw = _post_json(
            url=f"{self.base_url}/responses",
            payload=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            provider_name="OpenAI",
        )
        answer = _extract_openai_text(raw)
        return GenerationResult(answer=answer, model=self.model_name, raw=raw)


class AnthropicMessagesClient:
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 120,
        max_retries: int = 1,
        max_tokens: int = 4096,
        anthropic_version: str = "2023-06-01",
    ) -> None:
        self.model_name = model_name or os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.anthropic_version = anthropic_version

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        if not self.api_key:
            raise QuadModelError("ANTHROPIC_API_KEY is required for the Anthropic provider.")

        raw = _post_json(
            url=f"{self.base_url}/v1/messages",
            payload={
                "model": self.model_name,
                "max_tokens": self.max_tokens,
                "system": _join_instructions(system_prompt, metadata.get("developer_prompt", "")),
                "messages": [{"role": "user", "content": user_prompt}],
            },
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
                "Content-Type": "application/json",
            },
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            provider_name="Anthropic",
        )
        answer = _extract_anthropic_text(raw)
        return GenerationResult(answer=answer, model=self.model_name, raw=raw)


class GeminiClient:
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 120,
        max_retries: int = 1,
        max_output_tokens: int | None = None,
    ) -> None:
        self.model_name = model_name or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.base_url = (base_url or os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        if not self.api_key:
            raise QuadModelError("GEMINI_API_KEY or GOOGLE_API_KEY is required for the Gemini provider.")

        payload: dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": _join_instructions(system_prompt, metadata.get("developer_prompt", ""))}]
            },
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        }
        if self.max_output_tokens is not None:
            payload["generationConfig"] = {"maxOutputTokens": self.max_output_tokens}

        model_path = self.model_name if self.model_name.startswith("models/") else f"models/{self.model_name}"
        raw = _post_json(
            url=f"{self.base_url}/{model_path}:generateContent?key={self.api_key}",
            payload=payload,
            headers={"Content-Type": "application/json"},
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            provider_name="Gemini",
        )
        answer = _extract_gemini_text(raw)
        return GenerationResult(answer=answer, model=self.model_name, raw=raw)


def client_from_name(name: str, ollama_model: str | None = None, provider_model: str | None = None) -> LLMClient:
    normalized = name.lower()
    if normalized == "echo":
        return EchoLLMClient()
    if normalized == "ollama":
        return OllamaClient(model_name=provider_model or ollama_model or "llama3.1")
    if normalized == "openai":
        return OpenAIResponsesClient(model_name=provider_model)
    if normalized in {"anthropic", "claude"}:
        return AnthropicMessagesClient(model_name=provider_model)
    if normalized == "gemini":
        return GeminiClient(model_name=provider_model)
    raise QuadModelError(f"Unsupported model client: {name}")


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: int,
    max_retries: int,
    provider_name: str,
) -> dict[str, Any]:
    request_payload = json.dumps(payload).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        request = urllib.request.Request(url, data=request_payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise QuadModelError(f"{provider_name} request failed with HTTP {exc.code}: {body}") from exc
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt >= max_retries:
                raise QuadModelError(
                    f"{provider_name} request failed after {attempt + 1} attempt(s): {exc}"
                ) from exc
    raise QuadModelError(f"{provider_name} request failed: {last_error}")


def _join_instructions(system_prompt: str, developer_prompt: str) -> str:
    parts = [system_prompt.strip()]
    if developer_prompt.strip():
        parts.append(developer_prompt.strip())
    return "\n\n".join(parts)


def _extract_openai_text(raw: dict[str, Any]) -> str:
    output_text = raw.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    parts: list[str] = []
    for item in raw.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    answer = "\n".join(parts).strip()
    if not answer:
        raise QuadModelError("OpenAI returned no text output.")
    return answer


def _extract_anthropic_text(raw: dict[str, Any]) -> str:
    parts = [
        block["text"]
        for block in raw.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
    ]
    answer = "\n".join(parts).strip()
    if not answer:
        raise QuadModelError("Anthropic returned no text output.")
    return answer


def _extract_gemini_text(raw: dict[str, Any]) -> str:
    parts: list[str] = []
    for candidate in raw.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", {})
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []):
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
    answer = "\n".join(parts).strip()
    if not answer:
        raise QuadModelError("Gemini returned no text output.")
    return answer
