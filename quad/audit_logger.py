from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from quad.errors import QuadAuditLogError
from quad.models import GenerationResult, PromptBundle, RouterDecision, ScoreResult, ToolPlan

DEFAULT_AUDIT_DIR = Path(__file__).resolve().parents[1] / "logs" / "audit_logs"
AUDIT_SCHEMA_VERSION = "1.0"


def write_audit_log(
    query: str,
    decision: RouterDecision,
    tool_plan: ToolPlan,
    prompt: PromptBundle,
    generation: GenerationResult,
    score: ScoreResult,
    audit_dir: str | Path | None = None,
    redactions: list[str] | None = None,
) -> Path:
    output_dir = Path(audit_dir or DEFAULT_AUDIT_DIR)

    run_id = f"quad_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    log: dict[str, Any] = {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "query": query,
        "mode": decision.mode,
        "activation_reasons": decision.activation_reasons,
        "output_profile": decision.output_profile,
        "tools_required": tool_plan.required,
        "tool_reasons": tool_plan.reasons,
        "model": generation.model,
        "prompt_hash": _sha256({"system": prompt.system_prompt, "developer": prompt.developer_prompt, "user": prompt.user_prompt}),
        "yaml_version": prompt.metadata.get("yaml_version"),
        "answer": generation.answer,
        "failure_checks": [check.__dict__ for check in score.checks],
        "score": score.score,
        "decision": score.decision,
    }
    log = _redact_log(log, redactions or [])
    log["audit_hash"] = _sha256(log)

    path = output_dir / f"{run_id}.json"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(log, indent=2, sort_keys=True), encoding="utf-8")
    except OSError as exc:
        raise QuadAuditLogError(f"Failed to write audit log to `{output_dir}`: {exc}") from exc
    return path


def _sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _redact_log(log: dict[str, Any], redactions: list[str]) -> dict[str, Any]:
    if not redactions:
        return log
    redacted = json.loads(json.dumps(log, default=str))
    for path in redactions:
        _redact_path(redacted, path.split("."))
    return redacted


def _redact_path(value: Any, parts: list[str]) -> None:
    if not parts:
        return
    key = parts[0]
    if isinstance(value, dict):
        if len(parts) == 1 and key in value:
            value[key] = "[REDACTED]"
            return
        if key in value:
            _redact_path(value[key], parts[1:])
    elif isinstance(value, list):
        for item in value:
            _redact_path(item, parts)
