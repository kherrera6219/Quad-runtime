from __future__ import annotations

import json
from pathlib import Path

from quad.audit_logger import AUDIT_SCHEMA_VERSION
from quad.models import RuntimeRequest
from quad.runtime import QuadRuntime


def test_audit_log_includes_schema_version(tmp_path, monkeypatch):
    import quad.audit_logger as audit_logger
    import quad.runtime as runtime_module

    monkeypatch.setattr(audit_logger, "DEFAULT_AUDIT_DIR", tmp_path)
    monkeypatch.setattr(runtime_module, "write_audit_log", audit_logger.write_audit_log)

    result = QuadRuntime().run("Build a runtime architecture.")

    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    assert audit["audit_schema_version"] == AUDIT_SCHEMA_VERSION


def test_audit_redacts_requested_paths(tmp_path, monkeypatch):
    import quad.audit_logger as audit_logger
    import quad.runtime as runtime_module

    monkeypatch.setattr(audit_logger, "DEFAULT_AUDIT_DIR", tmp_path)
    monkeypatch.setattr(runtime_module, "write_audit_log", audit_logger.write_audit_log)

    result = QuadRuntime().run(
        RuntimeRequest(
            query="secret query",
            audit_redactions=["query", "answer"],
        )
    )

    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    assert audit["query"] == "[REDACTED]"
    assert audit["answer"] == "[REDACTED]"
    assert audit["audit_hash"]
