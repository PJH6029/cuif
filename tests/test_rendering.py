from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cuif_eval.pptx import render
from cuif_eval.pptx.render import render_pptx_previews


def test_structured_fallback_is_available_without_host_renderer(monkeypatch, toy_task, tmp_path):
    monkeypatch.setattr(render.shutil, "which", lambda name: None)

    result = render_pptx_previews(toy_task / "mock_outputs" / "final" / "result.pptx", tmp_path / "previews", "final")
    assert result["status"] == "fallback"
    assert Path(result["summary"]).exists()
    assert Path(result["html"]).exists()
    assert result["images"] == []
    assert "message" in result
    summary = json.loads(Path(result["summary"]).read_text(encoding="utf-8"))
    assert summary["slide_count"] > 0


def test_libreoffice_rendering_uses_isolated_profile_by_default(monkeypatch, toy_task, tmp_path):
    commands: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        return {"/fake/soffice": "/fake/soffice", "soffice": "/fake/soffice", "pdftoppm": "/fake/pdftoppm"}.get(name)

    def fake_run(command: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[0] == "/fake/soffice":
            outdir = Path(command[command.index("--outdir") + 1])
            (outdir / "result.pdf").write_bytes(b"%PDF fake")
        elif command[0] == "/fake/pdftoppm":
            prefix = Path(command[-1])
            (prefix.parent / f"{prefix.name}-1.png").write_bytes(b"png")
            (prefix.parent / f"{prefix.name}-2.png").write_bytes(b"png")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(render.shutil, "which", fake_which)
    monkeypatch.setattr(render, "_run", fake_run)

    result = render_pptx_previews(toy_task / "mock_outputs" / "final" / "result.pptx", tmp_path / "previews", "final")

    soffice_commands = [command for command in commands if command[0] == "/fake/soffice"]
    assert result["status"] == "rendered"
    assert len(soffice_commands) == 1
    assert any(arg.startswith("-env:UserInstallation=file://") for arg in soffice_commands[0])


def test_renderer_timeout_kills_process_group(monkeypatch):
    calls: dict[str, object] = {}

    class FakeProcess:
        pid = 12345
        returncode = None

        def __init__(self) -> None:
            self.communicate_calls = 0

        def communicate(self, *, timeout: int | None = None):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(["fake-soffice"], timeout)
            self.returncode = -9
            return "partial stdout", "partial stderr"

    fake_process = FakeProcess()

    def fake_popen(command, **kwargs):
        calls["command"] = command
        calls["kwargs"] = kwargs
        return fake_process

    def fake_killpg(pid, sig):
        calls["killpg"] = (pid, sig)

    monkeypatch.setattr(render.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(render.os, "killpg", fake_killpg)

    completed = render._run(["fake-soffice"], timeout=1)

    assert completed.returncode == -9
    assert completed.stdout == "partial stdout"
    assert "partial stderr" in completed.stderr
    assert "timed out after 1s" in completed.stderr
    assert calls["killpg"] == (12345, render.signal.SIGKILL)
    if hasattr(render.os, "setsid"):
        assert calls["kwargs"]["start_new_session"] is True
