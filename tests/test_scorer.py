from quad.failure_checks import run_failure_checks
from quad.scorer import score_answer


def test_clean_answer_scores_accept():
    checks = run_failure_checks("Recommendation: build the loader first. Confidence: Medium.", tool_required=False)
    score = score_answer(checks)

    assert score.score >= 85
    assert score.decision == "accept"


def test_bad_answer_scores_lower():
    checks = run_failure_checks(
        "Our panel of experts universally agree. Here is my internal reasoning. It depends.",
        tool_required=True,
    )
    score = score_answer(checks)

    assert score.score < 70
    assert score.decision in {"revise", "reject"}
