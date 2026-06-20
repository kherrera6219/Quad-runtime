from __future__ import annotations

from quad.models import Mode, OutputProfile, RouterDecision

HIGH_STAKES = {
    "legal",
    "medical",
    "financial",
    "security",
    "safety",
    "compliance",
    "production",
    "risk",
    "incident",
}
ARCHITECTURE = {
    "architecture",
    "design",
    "framework",
    "system",
    "runtime",
    "router",
    "workflow",
    "pipeline",
    "middleware",
}
TRADEOFF = {"tradeoff", "trade-off", "compare", "pros", "cons", "choose", "decision", "evaluate"}
IMPLEMENTATION = {"build", "implement", "code", "ship", "deploy", "integrate", "mvp", "cli", "api"}
MULTIPLE_STANDARDS = {"policy", "standard", "regulation", "ethics", "stakeholder", "governance"}


def route_query(
    query: str,
    mode: Mode = "auto",
    profile: OutputProfile | None = None,
    explicit_quad_request: bool = False,
) -> RouterDecision:
    text = query.lower()
    reasons = _activation_reasons(text, query)

    if mode == "quad" or explicit_quad_request:
        resolved = "quad"
        if not reasons:
            reasons = ["explicit_quad_request"]
    elif mode == "normal":
        resolved = "normal"
    else:
        resolved = "quad" if len(reasons) >= 2 else "normal"

    selected_profile = profile or _select_profile(resolved, reasons, query)
    return RouterDecision(mode=resolved, activation_reasons=reasons, output_profile=selected_profile)


def _activation_reasons(text: str, original: str) -> list[str]:
    reasons: list[str] = []
    if _contains_any(text, HIGH_STAKES):
        reasons.append("high_stakes")
    if _contains_any(text, ARCHITECTURE):
        reasons.append("architecture_or_design")
    if _contains_any(text, TRADEOFF):
        reasons.append("tradeoff_required")
    if _contains_any(text, IMPLEMENTATION):
        reasons.append("implementation_guidance")
    if len(original.split()) >= 160 or len(original) >= 1200:
        reasons.append("substantial_draft")
    if _contains_any(text, MULTIPLE_STANDARDS):
        reasons.append("multiple_standards")
    return reasons


def _select_profile(mode: str, reasons: list[str], query: str) -> OutputProfile:
    if mode == "normal":
        return "quick"
    if "substantial_draft" in reasons or len(query) >= 2000:
        return "deep"
    if {"architecture_or_design", "tradeoff_required", "implementation_guidance"}.issubset(set(reasons)):
        return "deep"
    return "standard"


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)
