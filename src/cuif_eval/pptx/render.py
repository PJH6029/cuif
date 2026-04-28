from __future__ import annotations

import html
import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .extract import summarize_pptx


def _trim(text: str) -> str:
    return text[-2000:]


def _clear_render_outputs(target_dir: Path) -> None:
    for pattern in ("*.png", "*.pdf"):
        for path in target_dir.glob(pattern):
            path.unlink(missing_ok=True)


def _run(command: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    popen_kwargs: dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }
    if hasattr(os, "setsid"):
        popen_kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **popen_kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        try:
            if hasattr(os, "killpg"):
                os.killpg(process.pid, signal.SIGKILL)
            else:  # pragma: no cover - non-POSIX fallback
                process.kill()
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        message = f"Command timed out after {timeout}s; killed renderer process group."
        return subprocess.CompletedProcess(
            command,
            process.returncode if process.returncode is not None else -signal.SIGKILL,
            stdout or "",
            f"{stderr or ''}\n{message}".strip(),
        )


def _libreoffice_command(renderer: str, profile_dir: Path, args: list[str]) -> list[str]:
    profile_uri = profile_dir.resolve().as_uri()
    return [renderer, f"-env:UserInstallation={profile_uri}", "--headless", *args]


def _render_pdf_pages(renderer: str, profile_dir: Path, pdftoppm: str, pptx_path: Path, target_dir: Path) -> tuple[list[str], dict[str, str]]:
    pdf_result = _run(_libreoffice_command(renderer, profile_dir, ["--convert-to", "pdf", "--outdir", str(target_dir), str(pptx_path)]))
    pdfs = sorted(target_dir.glob("*.pdf"))
    evidence = {"stdout": _trim(pdf_result.stdout), "stderr": _trim(pdf_result.stderr), "libreoffice_profile": "isolated_temp"}
    if pdf_result.returncode != 0 or not pdfs:
        return [], evidence
    prefix = target_dir / "slide"
    page_result = _run([pdftoppm, "-png", "-r", "144", str(pdfs[0]), str(prefix)])
    evidence.update({"pdftoppm_stdout": _trim(page_result.stdout), "pdftoppm_stderr": _trim(page_result.stderr)})
    if page_result.returncode != 0:
        return [], evidence
    return sorted(path.as_posix() for path in target_dir.glob("slide-*.png")), evidence


def _render_direct_png(renderer: str, profile_dir: Path, pptx_path: Path, target_dir: Path) -> tuple[list[str], dict[str, str]]:
    completed = _run(_libreoffice_command(renderer, profile_dir, ["--convert-to", "png", "--outdir", str(target_dir), str(pptx_path)]))
    evidence = {"stdout": _trim(completed.stdout), "stderr": _trim(completed.stderr), "libreoffice_profile": "isolated_temp"}
    if completed.returncode != 0:
        return [], evidence
    return sorted(path.as_posix() for path in target_dir.glob("*.png")), evidence


def render_pptx_previews(pptx_path: str | Path, previews_dir: str | Path, label: str) -> dict[str, Any]:
    """Best-effort PPTX preview generation with deterministic summary fallback.

    LibreOffice is optional. When LibreOffice and Poppler's ``pdftoppm`` are
    available, the renderer converts PPTX -> PDF -> PNG so every slide gets a
    navigable image. The fallback summary is always generated so CI does not
    depend on host rendering tools.
    """
    pptx_path = Path(pptx_path)
    previews_dir = Path(previews_dir)
    previews_dir.mkdir(parents=True, exist_ok=True)
    safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
    target_dir = previews_dir / safe_label
    target_dir.mkdir(parents=True, exist_ok=True)
    _clear_render_outputs(target_dir)

    summary = summarize_pptx(pptx_path)
    summary_path = target_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    html_path = target_dir / "summary.html"
    rows = "".join(
        f"<li>Slide {slide['slide']}: {html.escape(' | '.join(slide['text']))}</li>"
        for slide in summary["slides"]
    )
    html_path.write_text(
        "<!doctype html><meta charset='utf-8'>"
        f"<h3>{html.escape(label)}</h3><p>{html.escape(str(pptx_path))}</p>"
        f"<p>Slides: {summary['slide_count']} Shapes: {summary['shape_count']}</p><ul>{rows}</ul>",
        encoding="utf-8",
    )

    renderer = shutil.which("soffice") or shutil.which("libreoffice")
    if renderer is None:
        return {
            "status": "fallback",
            "renderer": None,
            "summary": summary_path.as_posix(),
            "html": html_path.as_posix(),
            "images": [],
            "message": "LibreOffice/soffice not found; generated structured fallback summary.",
        }

    try:
        pdftoppm = shutil.which("pdftoppm")
        expected_slide_count = int(summary.get("slide_count", 0))
        with tempfile.TemporaryDirectory(prefix="cuif-lo-profile-") as profile:
            profile_dir = Path(profile)
            if pdftoppm:
                images, evidence = _render_pdf_pages(renderer, profile_dir, pdftoppm, pptx_path, target_dir)
                if images and len(images) >= expected_slide_count:
                    return {
                        "status": "rendered",
                        "renderer": renderer,
                        "page_renderer": pdftoppm,
                        "summary": summary_path.as_posix(),
                        "html": html_path.as_posix(),
                        "images": images,
                        **evidence,
                    }

            images, evidence = _render_direct_png(renderer, profile_dir, pptx_path, target_dir)
            if images and len(images) >= expected_slide_count:
                return {
                    "status": "rendered",
                    "renderer": renderer,
                    "summary": summary_path.as_posix(),
                    "html": html_path.as_posix(),
                    "images": images,
                    **evidence,
                }
            return {
                "status": "fallback",
                "renderer": renderer,
                "summary": summary_path.as_posix(),
                "html": html_path.as_posix(),
                "images": images,
                "message": "Renderer did not produce one PNG per slide; generated fallback summary.",
                **evidence,
            }
    except Exception as exc:  # pragma: no cover - host renderer failures vary
        return {
            "status": "fallback",
            "renderer": renderer,
            "summary": summary_path.as_posix(),
            "html": html_path.as_posix(),
            "images": [],
            "message": f"Preview rendering failed: {exc}",
        }
