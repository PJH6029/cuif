from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import ADAPTERS
from .artifacts import RunWorkspace, create_run_workspace, read_run_metadata, validate_task_dir, write_run_metadata
from .reports import write_reports
from .schema import load_manifest
from .scoring import evaluate_manifest
from .types import CheckResult


def default_run_dir(task_id: str, adapter: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("output") / "runs" / f"{task_id}_{adapter}_{stamp}"


def run_task(task_dir: str | Path, *, adapter_name: str = "mock", out: str | Path | None = None, invocation_mode: str = "per_turn", skip_judges: bool = False, judge_base_url: str | None = None, judge_model: str | None = None, judge_api_key_env: str = "OPENAI_API_KEY", refresh_judge_cache: bool = False, adapter_config: dict[str, Any] | None = None) -> dict[str, Any]:
    task_dir = validate_task_dir(task_dir)
    manifest = load_manifest(task_dir / "manifest.yaml", skip_judges=skip_judges)
    run_dir = Path(out).resolve() if out is not None else default_run_dir(manifest.id, adapter_name).resolve()
    workspace = create_run_workspace(task_dir, run_dir)
    adapter_cls = ADAPTERS.get(adapter_name)
    if adapter_cls is None:
        raise ValueError(f"unknown adapter: {adapter_name}")
    adapter = adapter_cls()
    adapter_result = adapter.run(manifest, workspace, invocation_mode=invocation_mode, config=adapter_config or {})
    metadata = {
        "task_id": manifest.id,
        "task_dir": str(task_dir),
        "manifest_path": str(manifest.path),
        "adapter": adapter_name,
        "adapter_status": adapter_result.status,
        "invocation_mode": invocation_mode,
        "workspace": workspace.as_dict(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "adapter_result": adapter_result.to_json(),
        "judge": {"skip_judges": skip_judges, "base_url": judge_base_url, "model": judge_model, "api_key_env": judge_api_key_env},
    }
    write_run_metadata(workspace, metadata)
    results: list[CheckResult] = []
    report_paths: dict[str, Path] = {}
    if adapter_name != "manual":
        results = evaluate_manifest(manifest, workspace, skip_judges=skip_judges, judge_base_url=judge_base_url, judge_model=judge_model, judge_api_key_env=judge_api_key_env, refresh_judge_cache=refresh_judge_cache)
        (workspace.run_dir / "evaluation_results.json").write_text(json.dumps([r.to_json() for r in results], indent=2, sort_keys=True), encoding="utf-8")
        report_paths = write_reports(manifest, workspace, results)
    return {"manifest": manifest, "workspace": workspace, "adapter_result": adapter_result, "results": results, "report_paths": report_paths}


def evaluate_run(task_dir: str | Path, run_dir: str | Path, *, skip_judges: bool = False, judge_base_url: str | None = None, judge_model: str | None = None, judge_api_key_env: str = "OPENAI_API_KEY", refresh_judge_cache: bool = False) -> dict[str, Any]:
    task_dir = validate_task_dir(task_dir)
    manifest = load_manifest(task_dir / "manifest.yaml", skip_judges=skip_judges)
    run_dir = Path(run_dir).resolve()
    workspace = RunWorkspace(
        task_dir=task_dir,
        run_dir=run_dir,
        task_copy_dir=run_dir / "task",
        work_dir=run_dir / "work",
        outputs_dir=run_dir / "outputs",
        previews_dir=run_dir / "previews",
        judge_cache_dir=run_dir / "judge_cache",
        review_dir=run_dir / "review",
        logs_dir=run_dir / "logs",
    )
    for directory in (workspace.previews_dir, workspace.judge_cache_dir, workspace.review_dir, workspace.logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    metadata = read_run_metadata(run_dir)
    if not metadata:
        write_run_metadata(workspace, {"task_id": manifest.id, "task_dir": str(task_dir), "manifest_path": str(manifest.path), "adapter_status": "unknown"})
    results = evaluate_manifest(manifest, workspace, skip_judges=skip_judges, judge_base_url=judge_base_url, judge_model=judge_model, judge_api_key_env=judge_api_key_env, refresh_judge_cache=refresh_judge_cache)
    (workspace.run_dir / "evaluation_results.json").write_text(json.dumps([r.to_json() for r in results], indent=2, sort_keys=True), encoding="utf-8")
    report_paths = write_reports(manifest, workspace, results)
    return {"manifest": manifest, "workspace": workspace, "results": results, "report_paths": report_paths}


def regenerate_report(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir).resolve()
    report_json = run_dir / "report.json"
    if not report_json.exists():
        raise FileNotFoundError(f"report.json not found; run evaluate first: {report_json}")
    return json.loads(report_json.read_text(encoding="utf-8"))
