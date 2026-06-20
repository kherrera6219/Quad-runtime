from __future__ import annotations

import argparse
import sys

from quad.errors import QuadError
from quad.llm_client import client_from_name
from quad.runtime import QuadRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the QUAD reasoning runtime.")
    parser.add_argument("--query", required=True, help="User query to answer.")
    parser.add_argument("--mode", choices=["auto", "normal", "quad"], default="auto")
    parser.add_argument("--profile", choices=["quick", "standard", "deep"], default=None)
    parser.add_argument("--model", choices=["echo", "ollama", "openai", "anthropic", "claude", "gemini"], default="echo")
    parser.add_argument("--provider-model", default=None, help="Provider-specific model name override.")
    parser.add_argument("--ollama-model", default="llama3.1", help="Deprecated alias for Ollama model selection.")
    parser.add_argument("--no-audit", action="store_true", help="Do not write an audit log.")
    args = parser.parse_args()

    try:
        runtime = QuadRuntime(
            llm_client=client_from_name(
                args.model,
                ollama_model=args.ollama_model,
                provider_model=args.provider_model,
            )
        )
        result = runtime.run(
            query=args.query,
            mode=args.mode,  # type: ignore[arg-type]
            profile=args.profile,  # type: ignore[arg-type]
            audit=not args.no_audit,
        )
    except QuadError as exc:
        print(f"QUAD runtime error: {exc}", file=sys.stderr)
        return 1

    print(f"Mode: {result.mode.upper()}")
    print(f"Profile: {result.output_profile}")
    print(f"Model: {result.model}")
    print(f"Tools required: {str(result.tools_required).lower()}")
    print(f"Score: {result.score}")
    print(f"Decision: {result.decision}")
    if result.audit_path:
        print(f"Audit log saved: {result.audit_path}")
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print()
    print(result.answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
