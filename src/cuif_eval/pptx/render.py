from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .extract import summarize_pptx


def render_pptx_previews(pptx_path: str | Path, previews_dir: str | Path, label: str) -> dict[str, Any]:
    """Best-effort PPTX preview generation with deterministic summary fallback.

    LibreOffice is optional. The fallback summary is always generated so CI does not
    depend on host rendering tools.
    """
    pptx_path = Path(pptx_path)
    previews_dir = Path(previews_dir)
    previews_dir.mkdir(parents=True, exist_ok=True)
    safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
    target_dir = previews_dir / safe_label
    target_dir.mkdir(parents=True, exist_ok=True)
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
        completed = subprocess.run(
            [renderer, "--headless", "--convert-to", "png", "--outdir", str(target_dir), str(pptx_path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
        images = sorted(path.as_posix() for path in target_dir.glob("*.png"))
        if completed.returncode == 0 and images:
            return {
                "status": "rendered",
                "renderer": renderer,
                "summary": summary_path.as_posix(),
                "html": html_path.as_posix(),
                "images": images,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        return {
            "status": "fallback",
            "renderer": renderer,
            "summary": summary_path.as_posix(),
            "html": html_path.as_posix(),
            "images": images,
            "message": "LibreOffice did not produce PNG previews; generated fallback summary.",
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
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
