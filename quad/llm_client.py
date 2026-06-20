from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

from quad.errors import QuadModelError
from quad.models import GenerationResult


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


def client_from_name(name: str, ollama_model: str | None = None) -> LLMClient:
    if name == "echo":
        return EchoLLMClient()
    if name == "ollama":
        return OllamaClient(model_name=ollama_model or "llama3.1")
    raise QuadModelError(f"Unsupported model client: {name}")
