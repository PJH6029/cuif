from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .artifacts import RunWorkspace, output_reference, read_run_metadata, resolve_artifact_ref
from .pptx.render import render_pptx_previews
from .scoring import aggregate_results
from .types import CheckResult, Manifest


def _rel(path: str | Path, root: Path) -> str:
    path = Path(path)
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _portable(value: Any, manifest: Manifest, workspace: RunWorkspace) -> Any:
    """Rewrite run/task-local absolute paths in report payloads to portable links."""
    if isinstance(value, dict):
        return {key: _portable(item, manifest, workspace) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable(item, manifest, workspace) for item in value]
    if isinstance(value, str):
        run_root = workspace.run_dir.as_posix()
        task_root = manifest.task_dir.as_posix()
        text = value
        if text == run_root:
            text = "."
        text = text.replace(run_root + "/", "")
        if text == task_root:
            text = "task"
        text = text.replace(task_root + "/", "task/")
        return text
    return value


def collect_review_assets(manifest: Manifest, workspace: RunWorkspace) -> list[dict[str, Any]]:
    targets = manifest.review.get("comparison_targets") or []
    if not targets:
        targets = [
            {"label": "seed", "artifact": "package.seed"},
            {"label": "turn1 output", "artifact": "run.outputs.turn1.result"},
            {"label": "final output", "artifact": "run.outputs.final.result"},
            {"label": "gold final", "artifact": "package.gold_final"},
        ]
    assets: list[dict[str, Any]] = []
    for target in targets:
        artifact_ref = target.get("artifact")
        label = str(target.get("label", artifact_ref))
        try:
            path = resolve_artifact_ref(manifest, workspace, str(artifact_ref))
        except Exception as exc:
            assets.append({"label": label, "artifact": artifact_ref, "status": "error", "message": str(exc)})
            continue
        if not path.exists():
            assets.append({"label": label, "artifact": artifact_ref, "path": _rel(path, workspace.run_dir), "status": "missing", "message": "artifact missing"})
            continue
        preview = render_pptx_previews(path, workspace.previews_dir, label)
        preview_rel = {key: _rel(value, workspace.run_dir) if key in {"summary", "html"} and value else value for key, value in preview.items() if key != "images"}
        preview_rel["images"] = [_rel(image, workspace.run_dir) for image in preview.get("images", [])]
        assets.append({"label": label, "artifact": artifact_ref, "path": _rel(path, workspace.run_dir), "status": preview.get("status"), "preview": preview_rel})
    return assets


def build_report_data(manifest: Manifest, workspace: RunWorkspace, results: list[CheckResult]) -> dict[str, Any]:
    metadata = _portable(read_run_metadata(workspace.run_dir), manifest, workspace)
    review_assets = collect_review_assets(manifest, workspace)
    summary = aggregate_results(results)
    artifact_links: dict[str, str] = {}
    for name in manifest.package_artifacts:
        ref = f"package.{name}"
        artifact_links[ref] = output_reference(manifest, workspace, ref)
    for turn_id, outputs in manifest.expected_outputs.items():
        for output_name in outputs:
            ref = f"run.outputs.{turn_id}.{output_name}"
            artifact_links[ref] = output_reference(manifest, workspace, ref)
    manifest_link = "task/manifest.yaml" if (workspace.task_copy_dir / "manifest.yaml").exists() else str(manifest.path)
    return {
        "schema_version": "0.1",
        "task": {"id": manifest.id, "title": manifest.title, "manifest": manifest_link},
        "run": metadata,
        "summary": summary,
        "checks": _portable([result.to_json() for result in results], manifest, workspace),
        "artifacts": _portable(artifact_links, manifest, workspace),
        "review_assets": _portable(review_assets, manifest, workspace),
    }


def write_report_json(report_data: dict[str, Any], workspace: RunWorkspace) -> Path:
    path = workspace.run_dir / "report.json"
    path.write_text(json.dumps(report_data, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_report_md(report_data: dict[str, Any], workspace: RunWorkspace) -> Path:
    path = workspace.run_dir / "report.md"
    lines = [f"# CUIF Evaluation Report: {report_data['task']['title']}", ""]
    summary = report_data["summary"]
    lines += [
        f"- Task: `{report_data['task']['id']}`",
        f"- Score: {summary['earned_points']:.2f} / {summary['possible_points']:.2f} ({summary['final_score']:.1%})",
        f"- Status counts: `{summary['status_counts']}`",
        f"- Blocked checks: {', '.join(summary['blocked_checks']) if summary['blocked_checks'] else 'none'}",
        f"- Preservation/regression failures: {', '.join(summary['preservation_failures']) if summary['preservation_failures'] else 'none'}",
        "",
        "## Per-turn scores",
        "",
        "| Turn | Earned | Possible | Score | Status counts |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for turn_id, turn_summary in summary["per_turn"].items():
        lines.append(f"| {turn_id} | {turn_summary['earned_points']:.2f} | {turn_summary['possible_points']:.2f} | {turn_summary['score']:.1%} | `{turn_summary['status_counts']}` |")
    lines += ["", "## Checks", "", "| Turn | Check | Evaluator | Status | Points | Message |", "| --- | --- | --- | --- | ---: | --- |"]
    for check in report_data["checks"]:
        lines.append(f"| {check['turn_id']} | {check['check_id']} | {check['evaluator']} | {check['status']} | {check['earned_points']:.2f}/{check['points']:.2f} | {check['message']} |")
    lines += ["", "## Review assets", ""]
    for asset in report_data["review_assets"]:
        lines.append(f"- **{asset.get('label')}** `{asset.get('artifact')}`: {asset.get('status')} ({asset.get('path', 'n/a')})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_review_html(report_data: dict[str, Any], workspace: RunWorkspace) -> Path:
    path = workspace.review_dir / "index.html"
    summary = report_data["summary"]
    check_rows = "".join(
        "<tr>"
        f"<td>{html.escape(c['turn_id'])}</td><td>{html.escape(c['check_id'])}</td><td>{html.escape(c['evaluator'])}</td>"
        f"<td class='{html.escape(c['status'])}'>{html.escape(c['status'])}</td><td>{c['earned_points']:.2f}/{c['points']:.2f}</td>"
        f"<td>{html.escape(c['message'])}</td>"
        "</tr>"
        for c in report_data["checks"]
    )
    asset_cards = []
    for asset in report_data["review_assets"]:
        preview = asset.get("preview", {}) if isinstance(asset.get("preview"), dict) else {}
        images = preview.get("images", []) or []
        image_html = "".join(f"<img src='../{html.escape(image)}' alt='{html.escape(asset.get('label', 'preview'))}'>" for image in images)
        fallback = preview.get("html")
        fallback_html = f"<iframe src='../{html.escape(fallback)}'></iframe>" if fallback else f"<pre>{html.escape(asset.get('message', 'no preview'))}</pre>"
        asset_cards.append(
            "<section class='asset'>"
            f"<h3>{html.escape(str(asset.get('label')))}</h3>"
            f"<p><code>{html.escape(str(asset.get('artifact')))}</code> — {html.escape(str(asset.get('status')))}</p>"
            f"<p><a href='../{html.escape(str(asset.get('path', '')))}'>artifact</a></p>"
            f"{image_html or fallback_html}"
            "</section>"
        )
    html_text = f"""<!doctype html>
<meta charset="utf-8">
<title>CUIF Review: {html.escape(report_data['task']['title'])}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #172033; }}
.summary {{ padding: 1rem; background: #eef5ff; border-radius: 8px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
.asset {{ border: 1px solid #ccd5e0; border-radius: 8px; padding: 1rem; background: #fff; }}
img {{ max-width: 100%; border: 1px solid #ddd; }}
iframe {{ width: 100%; min-height: 240px; border: 1px solid #ddd; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
th, td {{ border: 1px solid #ddd; padding: .4rem; vertical-align: top; }}
.pass {{ color: #087f23; font-weight: 700; }} .fail, .error {{ color: #b00020; font-weight: 700; }} .blocked {{ color: #9a6700; font-weight: 700; }} .skipped {{ color: #5f6368; }}
</style>
<h1>CUIF Human Review</h1>
<div class="summary"><strong>Score:</strong> {summary['earned_points']:.2f} / {summary['possible_points']:.2f} ({summary['final_score']:.1%})<br><strong>Status counts:</strong> {html.escape(str(summary['status_counts']))}</div>
<h2>Seed / Output / Gold Comparison</h2>
<div class="grid">{''.join(asset_cards)}</div>
<h2>Check Results</h2>
<table><thead><tr><th>Turn</th><th>Check</th><th>Evaluator</th><th>Status</th><th>Points</th><th>Message</th></tr></thead><tbody>{check_rows}</tbody></table>
"""
    path.write_text(html_text, encoding="utf-8")
    return path


def write_reports(manifest: Manifest, workspace: RunWorkspace, results: list[CheckResult]) -> dict[str, Path]:
    data = build_report_data(manifest, workspace, results)
    return {
        "report_json": write_report_json(data, workspace),
        "report_md": write_report_md(data, workspace),
        "review_html": write_review_html(data, workspace),
    }
