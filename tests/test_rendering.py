from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cuif_eval.pptx import render
from cuif_eval.pptx.render import render_pptx_previews


def test_png_rendering_or_structured_fallback_is_available(toy_task, tmp_path):
    result = render_pptx_previews(toy_task / "mock_outputs" / "final" / "result.pptx", tmp_path / "previews", "final")
    assert result["status"] in {"rendered", "fallback"}
    assert Path(result["summary"]).exists()
    assert Path(result["html"]).exists()
    if result["status"] == "rendered":
        assert result["images"], result
        summary = json.loads(Path(result["summary"]).read_text(encoding="utf-8"))
        assert len(result["images"]) >= summary["slide_count"]
        assert all(Path(image).suffix == ".png" and Path(image).exists() for image in result["images"])
    else:
        assert result["images"] == []
        assert "message" in result


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
