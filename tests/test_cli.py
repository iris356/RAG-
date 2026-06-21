from __future__ import annotations

import subprocess

from rag_app import cli


def test_cli_forwards_streamlit_arguments(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_call(command, env):
        captured["command"] = command
        captured["env"] = env
        return 0

    monkeypatch.setattr(subprocess, "call", fake_call)
    monkeypatch.setattr(
        "sys.argv",
        ["rag-app", "--server.headless", "true", "--server.port", "8501"],
    )

    assert cli.main() == 0

    command = captured["command"]
    env = captured["env"]
    assert command[-4:] == ["--server.headless", "true", "--server.port", "8501"]
    assert env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] == "false"
