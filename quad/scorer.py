from __future__ import annotations

from quad.models import Decision, FailureCheckResult, ScoreResult

PENALTIES = {
    "unsupported_authority": 20,
    "stale_fact_confidence": 20,
    "mushy_compromise": 15,
    "fake_panel": 15,
    "overformalization": 10,
    "visible_chain_of_thought": 30,
}


def score_answer(checks: list[FailureCheckResult]) -> ScoreResult:
    score = 100
    for check in checks:
        if not check.passed:
            score -= PENALTIES.get(check.name, 5)
    score = max(score, 0)
    return ScoreResult(score=score, decision=_decision(score), checks=checks)


def _decision(score: int) -> Decision:
    if score >= 85:
        return "accept"
    if score >= 70:
        return "accept_with_caveats"
    if score >= 50:
        return "revise"
    return "reject"
