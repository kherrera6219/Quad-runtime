from __future__ import annotations

import re

from quad.models import FailureCheckResult


def run_failure_checks(answer: str, tool_required: bool) -> list[FailureCheckResult]:
    return [
        check_fake_panel(answer),
        check_mushy_compromise(answer),
        check_unsupported_authority(answer),
        check_stale_fact_confidence(answer, tool_required),
        check_chain_of_thought_leak(answer),
        check_overformalization(answer),
    ]


def check_fake_panel(answer: str) -> FailureCheckResult:
    text = answer.lower()
    patterns = ["our panel", "the experts agreed", "i consulted", "as a team of experts"]
    evidence = _first_match(text, patterns)
    return _result("fake_panel", evidence is None, "medium", evidence or "No fake-panel language found.", "revise")


def check_mushy_compromise(answer: str) -> FailureCheckResult:
    text = answer.lower()
    patterns = ["it depends", "both options are equally good", "there is no right answer"]
    evidence = _first_match(text, patterns)
    return _result("mushy_compromise", evidence is None, "medium", evidence or "No unsupported compromise language found.", "revise")


def check_unsupported_authority(answer: str) -> FailureCheckResult:
    text = answer.lower()
    patterns = ["studies prove", "experts universally agree", "certified by", "guaranteed"]
    evidence = _first_match(text, patterns)
    return _result("unsupported_authority", evidence is None, "high", evidence or "No unsupported authority claim found.", "revise")


def check_stale_fact_confidence(answer: str, tool_required: bool) -> FailureCheckResult:
    if not tool_required:
        return _result("stale_fact_confidence", True, "high", "Tools were not required.", "accept")

    has_citation_or_limit = bool(re.search(r"\[[0-9]+\]|sources?:|as of|i cannot verify|not verified", answer, flags=re.I))
    evidence = "Tool grounding required, but answer lacks citations or freshness limitation."
    return _result("stale_fact_confidence", has_citation_or_limit, "high", "Freshness limitation or citation found." if has_citation_or_limit else evidence, "revise")


def check_chain_of_thought_leak(answer: str) -> FailureCheckResult:
    text = answer.lower()
    patterns = ["chain of thought", "step-by-step private reasoning", "hidden reasoning", "my internal reasoning"]
    evidence = _first_match(text, patterns)
    return _result("visible_chain_of_thought", evidence is None, "high", evidence or "No chain-of-thought leakage found.", "reject")


def check_overformalization(answer: str) -> FailureCheckResult:
    visible_process_terms = sum(answer.lower().count(term) for term in ("qe-100", "qe-200", "triage ->", "cast lenses"))
    passed = visible_process_terms == 0
    evidence = "Visible framework process leaked into answer." if not passed else "No excessive framework process found."
    return _result("overformalization", passed, "low", evidence, "revise")


def _result(name: str, passed: bool, severity: str, evidence: str, recommendation: str) -> FailureCheckResult:
    return FailureCheckResult(
        name=name,
        passed=passed,
        severity=severity,  # type: ignore[arg-type]
        evidence=evidence,
        recommendation="accept" if passed else recommendation,  # type: ignore[arg-type]
    )


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if pattern in text:
            return pattern
    return None
