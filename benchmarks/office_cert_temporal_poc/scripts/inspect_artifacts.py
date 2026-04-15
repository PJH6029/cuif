from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from common import RENDERS, ROOT, WORKSPACES, now_utc, write_json


OFFICE_ZIP_SUFFIXES = {".docx", ".pptx", ".xlsx", ".xlsm"}


def inspect_file(path: Path) -> dict:
    item = {
        "path": str(path),
        "suffix": path.suffix.lower(),
        "bytes": path.stat().st_size,
        "exists": path.exists(),
    }
    if path.suffix.lower() in OFFICE_ZIP_SUFFIXES:
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                item["zip_ok"] = bad is None
                item["zip_bad_member"] = bad
        except Exception as exc:
            item["zip_ok"] = False
            item["error"] = str(exc)
    elif path.suffix.lower() == ".hwp":
        item["hwp_header_hex"] = path.read_bytes()[:16].hex()
    return item


def render_with_libreoffice(path: Path, render_dir: Path) -> list[str]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice:
        return []
    render_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile:
        subprocess.run(
            [
                soffice,
                f"-env:UserInstallation=file://{profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(render_dir),
                str(path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
    pdf = render_dir / f"{path.stem}.pdf"
    rendered = []
    if pdf.exists():
        rendered.append(str(pdf.relative_to(ROOT)))
        if pdftoppm:
            prefix = render_dir / path.stem
            subprocess.run(
                [pdftoppm, "-png", str(pdf), str(prefix)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
            rendered.extend(str(p.relative_to(ROOT)) for p in sorted(render_dir.glob(f"{path.stem}-*.png")))
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    workspace = WORKSPACES / args.task
    outputs = workspace / "outputs"
    records = []
    for path in sorted(p for p in outputs.rglob("*") if p.is_file()) if outputs.exists() else []:
        record = inspect_file(path)
        if args.render and path.suffix.lower() in OFFICE_ZIP_SUFFIXES:
            record["rendered"] = render_with_libreoffice(path, RENDERS / args.task / path.stem)
        records.append(record)
    report = {
        "generated_at": now_utc(),
        "task": args.task,
        "outputs_exists": outputs.exists(),
        "artifacts": records,
    }
    write_json(workspace / "run" / "artifact_inspection.json", report)
    print(f"Inspected {len(records)} artifacts for {args.task}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
