from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from common import (
    GOLD,
    METADATA_CACHE,
    ROOT,
    UNPACKED_CACHE,
    WORKSPACES,
    clean_dir,
    copy_file_unique,
    ensure_dirs,
    is_archive,
    load_yaml,
    read_json,
    role_from_name,
    safe_id,
    write_json,
    write_text,
)


PROFILE_GUIDANCE = {
    "spreadsheet": """Use the spreadsheet skill workflow. Prefer openpyxl/pandas for structured workbook edits, preserve formulas and formatting, and render through LibreOffice when layout matters. If a workbook is password-protected, first use the password stated in the problem PDF with msoffcrypto-tool or an equivalent local mechanism. Wrap LibreOffice commands with a timeout; if the workbook still cannot be opened, create outputs/BLOCKED_SPREADSHEET_ENV.md with the exact blocker. Save the final completed workbook under outputs/.""",
    "slides": """Use the slides skill workflow. Preserve editability where possible, use native PowerPoint structures for text/charts when practical, render slides for review, and save final PPTX artifacts under outputs/. Wrap LibreOffice render commands with a timeout and record any render blocker in outputs/NOTES.md.""",
    "doc": """Use the doc skill workflow. Prefer python-docx for DOCX work, render through LibreOffice/Poppler when possible, and save final DOCX/PDF artifacts under outputs/. Wrap conversion/render commands with a timeout and record any render blocker in outputs/NOTES.md.""",
    "hwp_mcp": """Use the repo-local hwp MCP server. This task requires Windows plus Hancom HWP. If the MCP server or HWP program is unavailable, create outputs/BLOCKED_HWP_MCP.md explaining the missing environment instead of fabricating a DOCX-only result.""",
}


def zip_members(zip_path: Path) -> list[tuple[str, bytes]]:
    members = []
    try:
        zf = zipfile.ZipFile(zip_path, metadata_encoding="cp949")
    except TypeError:
        zf = zipfile.ZipFile(zip_path)
    with zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name
            if not name or name.startswith("."):
                continue
            members.append((info.filename, zf.read(info)))
    return members


def unpack_archive(path: Path, dest: Path) -> list[Path]:
    clean_dir(dest)
    extracted = []
    if path.suffix.lower() != ".zip":
        copied = copy_file_unique(path, dest)
        return [copied]
    for raw_name, content in zip_members(path):
        rel = Path(*[part for part in Path(raw_name).parts if part not in ("", ".", "..")])
        if not rel.parts:
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        extracted.append(target)
    return extracted


def fetch_index() -> dict:
    path = METADATA_CACHE / "fetch_index.json"
    if not path.exists():
        raise SystemExit("Missing cache/metadata/fetch_index.json. Run fetch_sources.py first.")
    return read_json(path)


def find_task(task_id: str | None, enabled_only: bool) -> list[dict]:
    manifest = load_yaml(ROOT / "task_manifest.yml")
    tasks = manifest.get("tasks", [])
    if task_id:
        matches = [t for t in tasks if t["id"] == task_id]
        if not matches:
            raise SystemExit(f"Unknown task: {task_id}")
        return matches
    if enabled_only:
        return [t for t in tasks if t.get("enabled", True)]
    return tasks


def matching_downloads(task: dict, index: dict) -> list[dict]:
    source_id = task["source_id"]
    item_key = task.get("discovered_item")
    out = []
    for item in index.get("downloads", []):
        if item.get("source_id") != source_id:
            continue
        if item_key and item.get("item_key") != item_key:
            continue
        if item.get("status") != "downloaded":
            continue
        if "path" not in item:
            continue
        out.append(item)
    return out


def classify_download(item: dict, task: dict) -> list[dict]:
    source_path = ROOT / item["path"]
    if not source_path.exists():
        return [{"path": str(source_path), "role": "missing", "source": item}]
    unpack_id = safe_id(f'{task["id"]}__{item.get("download_id", source_path.stem)}')
    unpack_dir = UNPACKED_CACHE / unpack_id
    paths = unpack_archive(source_path, unpack_dir) if is_archive(source_path) else [source_path]
    classified = []
    for path in paths:
        role = item.get("role")
        if role in {"archive", "course_materials"}:
            role = role_from_name(path.name)
        classified.append({"path": path, "role": role, "source": item})
    return classified


def write_prompt(task: dict, workspace: Path, metadata: dict) -> None:
    profile = task.get("solver_profile", "")
    guidance = PROFILE_GUIDANCE.get(profile, "Use the relevant office artifact workflow.")
    input_listing = "\n".join(f"- {p['role']}: inputs/{Path(p['workspace_path']).name}" for p in metadata["solver_files"])
    text = f"""# Task: {task['id']}

You are solving an office certification practice task for the CUIF PoC.

Title: {task.get('title')}
Target application/artifact: {task.get('app_target')} / {task.get('artifact_type')}

## Files Available

{input_listing or "- No input files were prepared. Inspect TASK_METADATA.json for blockers."}

## Instructions

1. Work only inside this solver workspace.
2. Do not use files outside this workspace and do not search the internet.
3. Read the problem statement first, then inspect the source office files.
4. Keep all final deliverables in `outputs/`.
5. Preserve editability and native structure where possible.
6. Keep notes about any blocker or unimplemented item in `outputs/NOTES.md`.
7. Gold/model answer files are deliberately withheld from this workspace.

## Solver Guidance

{guidance}

## Success Note

{task.get('success_note', '')}
"""
    write_text(workspace / "TASK_PROMPT.md", text)


def prepare_task(task: dict, force: bool) -> dict:
    index = fetch_index()
    downloads = matching_downloads(task, index)
    workspace = WORKSPACES / task["id"]
    gold_dir = GOLD / task["id"]
    if workspace.exists() and not force:
        raise SystemExit(f"Workspace already exists: {workspace}. Use --force to recreate it.")
    clean_dir(workspace)
    clean_dir(gold_dir)
    (workspace / "inputs").mkdir(parents=True, exist_ok=True)
    (workspace / "outputs").mkdir(parents=True, exist_ok=True)
    (workspace / "run").mkdir(parents=True, exist_ok=True)

    classified = []
    for item in downloads:
        classified.extend(classify_download(item, task))

    solver_files = []
    gold_files = []
    missing = []
    for entry in classified:
        path = entry["path"]
        role = entry["role"]
        if isinstance(path, str):
            missing.append(entry)
            continue
        if role == "gold":
            dest = copy_file_unique(path, gold_dir)
            gold_files.append({**entry, "gold_path": str(dest.relative_to(ROOT)), "path": str(path.relative_to(ROOT))})
        else:
            dest = copy_file_unique(path, workspace / "inputs")
            solver_files.append(
                {
                    **entry,
                    "workspace_path": str(dest.relative_to(workspace)),
                    "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                }
            )

    metadata = {
        "task": task,
        "workspace": str(workspace.relative_to(ROOT)),
        "downloads": downloads,
        "solver_files": solver_files,
        "gold_files": gold_files,
        "missing": missing,
    }
    serializable = json.loads(json.dumps(metadata, default=str, ensure_ascii=False))
    write_json(workspace / "TASK_METADATA.json", serializable)
    write_json(gold_dir / "GOLD_METADATA.json", serializable)
    write_prompt(task, workspace, serializable)
    return serializable


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.task and not args.all:
        raise SystemExit("Pass --task <id> or --all.")
    ensure_dirs()
    tasks = find_task(args.task, enabled_only=not args.include_disabled)
    for task in tasks:
        if not task.get("enabled", True) and not args.include_disabled:
            print(f"Skipping disabled task: {task['id']}")
            continue
        result = prepare_task(task, force=args.force)
        print(
            f"Prepared {task['id']}: "
            f"{len(result['solver_files'])} solver files, {len(result['gold_files'])} gold files."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
