from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

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
    def __init__(self, model_name: str = "llama3.1", base_url: str = "http://localhost:11434") -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(self, system_prompt: str, user_prompt: str, metadata: dict[str, Any]) -> GenerationResult:
        prompt = f"System:\n{system_prompt}\n\nDeveloper:\n{metadata.get('developer_prompt', '')}\n\nUser:\n{user_prompt}"
        payload = json.dumps({"model": self.model_name, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama request failed at {self.base_url}: {exc}") from exc

        return GenerationResult(answer=raw.get("response", ""), model=self.model_name, raw=raw)


def client_from_name(name: str, ollama_model: str | None = None) -> LLMClient:
    if name == "echo":
        return EchoLLMClient()
    if name == "ollama":
        return OllamaClient(model_name=ollama_model or "llama3.1")
    raise ValueError(f"Unsupported model client: {name}")
