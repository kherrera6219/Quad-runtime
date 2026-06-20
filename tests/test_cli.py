from __future__ import annotations

from quad import cli
from quad.errors import QuadModelError


def test_cli_returns_nonzero_for_quad_errors(monkeypatch, capsys):
    monkeypatch.setattr(cli, "client_from_name", lambda *args, **kwargs: (_ for _ in ()).throw(QuadModelError("bad model")))
    monkeypatch.setattr("sys.argv", ["main.py", "--query=hello"])

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "QUAD runtime error: bad model" in captured.err
