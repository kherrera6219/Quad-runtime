from pathlib import Path

from quad.runtime import QuadRuntime


def test_runtime_writes_audit_log(tmp_path, monkeypatch):
    from quad import audit_logger
    import quad.runtime as runtime_module

    monkeypatch.setattr(audit_logger, "DEFAULT_AUDIT_DIR", tmp_path)
    monkeypatch.setattr(runtime_module, "write_audit_log", lambda *args, **kwargs: Path(tmp_path) / "audit.json")

    result = QuadRuntime().run("Build a runtime architecture and compare implementation tradeoffs.")

    assert result.mode == "quad"
    assert result.score >= 85
    assert result.audit_path is not None
