from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from quad.models import GenerationResult, PromptBundle, RouterDecision, ScoreResult, ToolPlan

DEFAULT_AUDIT_DIR = Path(__file__).resolve().parents[1] / "logs" / "audit_logs"


def write_audit_log(
    query: str,
    decision: RouterDecision,
    tool_plan: ToolPlan,
    prompt: PromptBundle,
    generation: GenerationResult,
    score: ScoreResult,
    audit_dir: str | Path = DEFAULT_AUDIT_DIR,
) -> Path:
    output_dir = Path(audit_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"quad_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    log: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    log["audit_hash"] = _sha256(log)

    path = output_dir / f"{run_id}.json"
    path.write_text(json.dumps(log, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
