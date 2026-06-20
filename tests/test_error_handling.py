from __future__ import annotations

from pathlib import Path

import pytest

from quad.audit_logger import write_audit_log
from quad.config_loader import return_config
from quad.errors import QuadAuditLogError, QuadConfigError, QuadModelError, QuadRoutingError
from quad.llm_client import client_from_name
from quad.models import GenerationResult, RuntimeRequest
from quad.runtime import QuadRuntime


def test_missing_config_file_raises_typed_error(tmp_path):
    with pytest.raises(QuadConfigError):
        return_config(tmp_path / "missing.yaml")


def test_malformed_config_schema_raises_typed_error(tmp_path):
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(
        """
quad_engine:
  version: "2.2"
  activation_policy: {}
  evidence_policy: {}
  tool_policy: {}
  role_policy: {}
  output_profiles:
    quick: {}
    standard: {}
    deep: {}
  failure_modes:
    avoid: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(QuadConfigError, match="visible_sections"):
        return_config(config_path)


def test_unknown_model_client_raises_typed_error():
    with pytest.raises(QuadModelError):
        client_from_name("unknown")


def test_empty_runtime_request_raises_typed_error():
    runtime = QuadRuntime()

    with pytest.raises(QuadRoutingError):
        runtime.run(RuntimeRequest(query=""))


def test_audit_failure_fails_closed_by_default(monkeypatch):
    import quad.runtime as runtime_module

    def fail_audit(*args, **kwargs):
        raise QuadAuditLogError("audit failed")

    monkeypatch.setattr(runtime_module, "write_audit_log", fail_audit)

    with pytest.raises(QuadAuditLogError):
        QuadRuntime().run("Build a runtime architecture.")


def test_audit_failure_can_return_warning_when_optional(monkeypatch):
    import quad.runtime as runtime_module

    def fail_audit(*args, **kwargs):
        raise QuadAuditLogError("audit failed")

    monkeypatch.setattr(runtime_module, "write_audit_log", fail_audit)

    result = QuadRuntime().run(RuntimeRequest(query="Build a runtime architecture.", audit_required=False))

    assert result.audit_path is None
    assert result.warnings == ["audit failed"]


def test_write_audit_log_wraps_os_errors(tmp_path, monkeypatch):
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()

    def fail_write_text(self, *args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    runtime = QuadRuntime()
    request = RuntimeRequest(query="Build a runtime architecture.", audit=False)
    result = runtime.run(request)

    from quad.prompt_builder import build_prompt
    from quad.router import route_query
    from quad.scorer import score_answer
    from quad.failure_checks import run_failure_checks
    from quad.tool_grounding import build_tool_plan

    decision = route_query(request.query)
    tool_plan = build_tool_plan(request.query, runtime.config)
    prompt = build_prompt(runtime.config, request.query, decision, tool_plan)
    generation = GenerationResult(answer=result.answer, model=result.model)
    score = score_answer(run_failure_checks(generation.answer, tool_required=False))

    with pytest.raises(QuadAuditLogError):
        write_audit_log(request.query, decision, tool_plan, prompt, generation, score, audit_dir=audit_dir)
