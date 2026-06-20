from quad.failure_checks import run_failure_checks


def test_failure_checks_detect_fake_panel():
    checks = run_failure_checks("Our panel of experts agreed this is guaranteed.", tool_required=False)
    failed = {check.name for check in checks if not check.passed}

    assert "fake_panel" in failed
    assert "unsupported_authority" in failed


def test_tool_required_answer_needs_citation_or_limitation():
    checks = run_failure_checks("The current price is 10.", tool_required=True)
    stale = next(check for check in checks if check.name == "stale_fact_confidence")

    assert stale.passed is False
