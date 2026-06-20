from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Mode = Literal["auto", "normal", "quad"]
ResolvedMode = Literal["normal", "quad"]
OutputProfile = Literal["quick", "standard", "deep"]
Decision = Literal["accept", "accept_with_caveats", "revise", "reject"]


@dataclass(frozen=True)
class RouterDecision:
    mode: ResolvedMode
    activation_reasons: list[str]
    output_profile: OutputProfile


@dataclass(frozen=True)
class ToolPlan:
    required: bool
    reasons: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PromptBundle:
    system_prompt: str
    developer_prompt: str
    user_prompt: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FailureCheckResult:
    name: str
    passed: bool
    severity: Literal["low", "medium", "high"]
    evidence: str
    recommendation: Decision


@dataclass(frozen=True)
class ScoreResult:
    score: int
    decision: Decision
    checks: list[FailureCheckResult]


@dataclass(frozen=True)
class RuntimeResult:
    answer: str
    mode: ResolvedMode
    activation_reasons: list[str]
    output_profile: OutputProfile
    tools_required: bool
    score: int
    decision: Decision
    audit_path: str | None
    model: str
