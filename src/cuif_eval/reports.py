from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from .artifacts import RunWorkspace, output_reference, read_run_metadata, resolve_artifact_ref
from .pptx.render import render_pptx_previews
from .scoring import aggregate_results, point_distribution
from .types import CheckResult, Manifest, TurnSpec


FINAL_TURN_ID = "final"


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


def _preview_rel(preview: dict[str, Any], workspace: RunWorkspace) -> dict[str, Any]:
    preview_rel = {
        key: _rel(value, workspace.run_dir) if key in {"summary", "html"} and value else value
        for key, value in preview.items()
        if key != "images"
    }
    preview_rel["images"] = [_rel(image, workspace.run_dir) for image in preview.get("images", [])]
    return preview_rel


def _artifact_type(manifest: Manifest, artifact_ref: str | None) -> str | None:
    if artifact_ref is None:
        return None
    parts = artifact_ref.split(".")
    if len(parts) == 2 and parts[0] == "package":
        artifact = manifest.package_artifacts.get(parts[1])
        return str(artifact.get("type")) if artifact else None
    if len(parts) == 4 and parts[:2] == ["run", "outputs"]:
        output = manifest.expected_outputs.get(parts[2], {}).get(parts[3])
        return str(output.get("type")) if output else None
    return None


def _package_ref(manifest: Manifest, artifact_name: str) -> str | None:
    return f"package.{artifact_name}" if artifact_name in manifest.package_artifacts else None


def _run_output_ref(manifest: Manifest, turn_id: str, output_name: str | None) -> str | None:
    outputs = manifest.expected_outputs.get(turn_id, {})
    candidates = [name for name in [output_name, "result"] if name]
    for candidate in candidates:
        if candidate in outputs:
            return f"run.outputs.{turn_id}.{candidate}"
    if len(outputs) == 1:
        only_name = next(iter(outputs))
        return f"run.outputs.{turn_id}.{only_name}"
    return None


def _turn_label(turn_id: str, ordinal: int | None = None) -> str:
    if turn_id == FINAL_TURN_ID:
        return "Final"
    match = re.fullmatch(r"turn(\d+)", turn_id)
    if match:
        return f"Turn {match.group(1)}"
    if ordinal is not None:
        return f"Turn {ordinal} ({turn_id})"
    return turn_id.replace("_", " ").replace("-", " ").title()


def _turn_gold_ref(manifest: Manifest, turn_id: str, ordinal: int) -> str | None:
    candidates = [f"gold_{turn_id}", f"gold_turn{ordinal}"]
    for candidate in dict.fromkeys(candidates):
        ref = _package_ref(manifest, candidate)
        if ref:
            return ref
    return None


def _final_output_ref(manifest: Manifest, final_turn: TurnSpec | None) -> str | None:
    if final_turn is not None:
        return _run_output_ref(manifest, FINAL_TURN_ID, final_turn.expected_output)
    return _run_output_ref(manifest, FINAL_TURN_ID, "result")


def _make_review_cell(
    manifest: Manifest,
    workspace: RunWorkspace,
    *,
    label: str,
    artifact_ref: str | None,
    role: str,
    missing_status: str = "missing",
    missing_message: str | None = None,
    placeholder_message: str | None = None,
) -> dict[str, Any]:
    if artifact_ref is None:
        status = "placeholder" if placeholder_message else missing_status
        return {
            "label": label,
            "artifact": None,
            "role": role,
            "status": status,
            "message": placeholder_message or missing_message or "Artifact is not declared.",
            "preview": {"images": []},
            "selectable": False,
        }

    artifact_type = _artifact_type(manifest, artifact_ref)
    try:
        path = resolve_artifact_ref(manifest, workspace, artifact_ref)
    except Exception as exc:
        return {
            "label": label,
            "artifact": artifact_ref,
            "role": role,
            "type": artifact_type,
            "status": "error",
            "message": str(exc),
            "preview": {"images": []},
            "selectable": False,
        }

    cell: dict[str, Any] = {
        "label": label,
        "artifact": artifact_ref,
        "role": role,
        "type": artifact_type,
        "path": _rel(path, workspace.run_dir),
    }
    if not path.exists():
        cell.update(
            {
                "status": missing_status,
                "message": missing_message or "Artifact missing or not produced.",
                "preview": {"images": []},
                "selectable": False,
            }
        )
        return cell

    if artifact_type == "pptx":
        preview = render_pptx_previews(path, workspace.previews_dir, label)
        cell.update(
            {
                "status": preview.get("status"),
                "message": preview.get("message"),
                "preview": _preview_rel(preview, workspace),
                "selectable": True,
            }
        )
        return cell

    cell.update(
        {
            "status": "available",
            "message": f"{artifact_type or 'artifact'} preview is not available in the trajectory view.",
            "preview": {"images": []},
            "selectable": True,
        }
    )
    return cell


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
        if _artifact_type(manifest, str(artifact_ref)) == "pptx":
            preview = render_pptx_previews(path, workspace.previews_dir, label)
            assets.append({"label": label, "artifact": artifact_ref, "path": _rel(path, workspace.run_dir), "status": preview.get("status"), "preview": _preview_rel(preview, workspace)})
        else:
            assets.append({"label": label, "artifact": artifact_ref, "path": _rel(path, workspace.run_dir), "status": "available", "preview": {"images": []}})
    return assets


def collect_review_trajectory(manifest: Manifest, workspace: RunWorkspace) -> dict[str, Any]:
    final_turn = next((turn for turn in manifest.turns if turn.id == FINAL_TURN_ID), None)
    non_final_turns = [turn for turn in manifest.turns if turn.id != FINAL_TURN_ID]

    columns: list[dict[str, Any]] = []
    seed_ref = _package_ref(manifest, "seed")
    columns.append(
        {
            "id": "seed",
            "label": "Seed",
            "instruction": None,
            "top": _make_review_cell(
                manifest,
                workspace,
                label="Seed deck",
                artifact_ref=seed_ref,
                role="seed",
                missing_status="missing",
                missing_message="Seed deck is not declared or is missing.",
            ),
            "bottom": _make_review_cell(
                manifest,
                workspace,
                label="No seed output",
                artifact_ref=None,
                role="output-placeholder",
                placeholder_message="Agent output starts after turn 1.",
            ),
        }
    )

    for ordinal, turn in enumerate(non_final_turns, start=1):
        turn_label = _turn_label(turn.id, ordinal)
        columns.append(
            {
                "id": turn.id,
                "label": turn_label,
                "instruction": turn.instruction,
                "top": _make_review_cell(
                    manifest,
                    workspace,
                    label=f"{turn_label} gold",
                    artifact_ref=_turn_gold_ref(manifest, turn.id, ordinal),
                    role="gold",
                    missing_status="missing",
                    missing_message=f"Gold artifact for {turn_label} is not declared.",
                ),
                "bottom": _make_review_cell(
                    manifest,
                    workspace,
                    label=f"{turn_label} output",
                    artifact_ref=_run_output_ref(manifest, turn.id, turn.expected_output),
                    role="output",
                    missing_status="not_produced",
                    missing_message=f"Agent output for {turn_label} was not produced.",
                ),
            }
        )

    if final_turn is not None or _package_ref(manifest, "gold_final") or FINAL_TURN_ID in manifest.expected_outputs:
        columns.append(
            {
                "id": FINAL_TURN_ID,
                "label": "Final",
                "instruction": final_turn.instruction if final_turn is not None else None,
                "top": _make_review_cell(
                    manifest,
                    workspace,
                    label="Final gold",
                    artifact_ref=_package_ref(manifest, "gold_final"),
                    role="gold-final",
                    missing_status="missing",
                    missing_message="Final gold artifact is not declared.",
                ),
                "bottom": _make_review_cell(
                    manifest,
                    workspace,
                    label="Final output",
                    artifact_ref=_final_output_ref(manifest, final_turn),
                    role="output-final",
                    missing_status="not_produced",
                    missing_message="Final agent output was not produced.",
                ),
            }
        )

    return {
        "version": 1,
        "columns": columns,
        "row_labels": {"instruction": "Instruction", "top": "Seed / gold", "bottom": "Agent output"},
    }


def build_report_data(manifest: Manifest, workspace: RunWorkspace, results: list[CheckResult]) -> dict[str, Any]:
    metadata = _portable(read_run_metadata(workspace.run_dir), manifest, workspace)
    review_assets = collect_review_assets(manifest, workspace)
    review_trajectory = collect_review_trajectory(manifest, workspace)
    summary = aggregate_results(results)
    distribution = point_distribution(manifest)
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
        "point_distribution": distribution,
        "checks": _portable([result.to_json() for result in results], manifest, workspace),
        "artifacts": _portable(artifact_links, manifest, workspace),
        "review_assets": _portable(review_assets, manifest, workspace),
        "review_trajectory": _portable(review_trajectory, manifest, workspace),
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
    distribution = report_data.get("point_distribution", {})
    if distribution:
        lines += [
            "",
            "## Point distribution",
            "",
            f"- Thesis-heavy points: {distribution['thesis_heavy_points']:.2f} / {distribution['review_points']:.2f} ({distribution['thesis_heavy_share']:.1%})",
            f"- Threshold: {distribution['threshold']:.0%}; meets threshold: `{distribution['meets_threshold']}`",
            f"- Excluded points: {distribution['excluded_points']:.2f} (`file_exists`, `pptx_slide_count`, and diagnostic preview checks)",
            f"- Buckets: `{distribution['buckets']}`",
        ]
    lines += ["", "## Checks", "", "| Turn | Check | Evaluator | Status | Points | Message |", "| --- | --- | --- | --- | ---: | --- |"]
    for check in report_data["checks"]:
        lines.append(f"| {check['turn_id']} | {check['check_id']} | {check['evaluator']} | {check['status']} | {check['earned_points']:.2f}/{check['points']:.2f} | {check['message']} |")
    lines += ["", "## Review assets", ""]
    for asset in report_data["review_assets"]:
        lines.append(f"- **{asset.get('label')}** `{asset.get('artifact')}`: {asset.get('status')} ({asset.get('path', 'n/a')})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _html_attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _status_class(status: Any) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", str(status or "unknown").lower())


def _render_legacy_asset_cards(report_data: dict[str, Any]) -> str:
    asset_cards = []
    for asset in report_data.get("review_assets", []):
        preview = asset.get("preview", {}) if isinstance(asset.get("preview"), dict) else {}
        images = preview.get("images", []) or []
        image_html = "".join(f"<img src='../{_html_attr(image)}' alt='{_html_attr(asset.get('label', 'preview'))}'>" for image in images)
        fallback = preview.get("html")
        fallback_html = f"<iframe src='../{_html_attr(fallback)}'></iframe>" if fallback else f"<pre>{html.escape(asset.get('message', 'no preview'))}</pre>"
        asset_cards.append(
            "<section class='asset'>"
            f"<h3>{html.escape(str(asset.get('label')))}</h3>"
            f"<p><code>{html.escape(str(asset.get('artifact')))}</code> — {html.escape(str(asset.get('status')))}</p>"
            f"<p><a href='../{_html_attr(asset.get('path', ''))}'>artifact</a></p>"
            f"{image_html or fallback_html}"
            "</section>"
        )
    if not asset_cards:
        return ""
    return "<details class='legacy-comparison'><summary>Legacy configured comparison targets</summary><div class='grid'>" + "".join(asset_cards) + "</div></details>"


def _render_trajectory_cell(cell: dict[str, Any], *, row: str, column_id: str) -> str:
    status = str(cell.get("status", "unknown"))
    selectable = bool(cell.get("selectable"))
    preview = cell.get("preview", {}) if isinstance(cell.get("preview"), dict) else {}
    images = [f"../{image}" for image in (preview.get("images", []) or [])]
    images_json = _html_attr(json.dumps(images))
    fallback = preview.get("html")
    path = cell.get("path")
    cell_id = f"{column_id}-{row}"
    classes = ["trajectory-cell", f"trajectory-cell--{_status_class(status)}"]
    if selectable:
        classes.append("trajectory-cell--selectable")
    else:
        classes.append("trajectory-cell--static")
    body = ""
    if images:
        body = f"<img class='trajectory-preview-image' src='{_html_attr(images[0])}' alt='{_html_attr(cell.get('label', 'preview'))}'>"
    elif fallback:
        body = f"<iframe class='trajectory-preview-frame' src='../{_html_attr(fallback)}'></iframe>"
    else:
        body = f"<div class='trajectory-missing-message'>{html.escape(str(cell.get('message') or 'No preview available.'))}</div>"
    artifact = cell.get("artifact") or "—"
    link_html = f"<a href='../{_html_attr(path)}'>artifact</a>" if path and status not in {"missing", "not_produced", "error"} else ""
    page_text = f"1 / {len(images)}" if images else ("summary" if fallback else "—")
    role_attr = "button" if selectable else "group"
    tab_index = "0" if selectable else "-1"
    return (
        f"<div class='{_html_attr(' '.join(classes))}' data-trajectory-cell data-cell-id='{_html_attr(cell_id)}' "
        f"data-column-id='{_html_attr(column_id)}' data-row='{_html_attr(row)}' data-selectable='{str(selectable).lower()}' "
        f"data-images='{images_json}' data-current-index='0' role='{role_attr}' tabindex='{tab_index}'>"
        f"<div class='trajectory-cell-header'><strong>{html.escape(str(cell.get('label')))}</strong><span class='trajectory-status'>{html.escape(status)}</span></div>"
        f"<div class='trajectory-artifact'><code>{html.escape(str(artifact))}</code>{link_html}</div>"
        f"<div class='trajectory-preview'>{body}</div>"
        f"<div class='trajectory-page-indicator' data-page-indicator>{html.escape(page_text)}</div>"
        "</div>"
    )


def _render_trajectory_instruction_cell(column: dict[str, Any]) -> str:
    column_id = str(column.get("id", ""))
    instruction = str(column.get("instruction") or "").strip()
    classes = ["trajectory-instruction-cell"]
    if instruction:
        body = html.escape(instruction)
    else:
        classes.append("trajectory-instruction-cell--empty")
        message = "Initial seed artifact" if column_id == "seed" else "No turn instruction declared."
        body = f"<span>{html.escape(message)}</span>"
    return (
        f"<div class='{_html_attr(' '.join(classes))}' data-trajectory-instruction='{_html_attr(column_id)}'>"
        f"{body}"
        "</div>"
    )


def _render_trajectory_comparison(report_data: dict[str, Any]) -> str:
    trajectory = report_data.get("review_trajectory", {}) if isinstance(report_data.get("review_trajectory"), dict) else {}
    columns = trajectory.get("columns", []) if isinstance(trajectory.get("columns"), list) else []
    if not columns:
        return "<h2>Trajectory Comparison</h2><p>No trajectory comparison data available.</p>"

    headers = "".join(f"<div class='trajectory-column-header' data-trajectory-column='{_html_attr(col.get('id'))}'>{html.escape(str(col.get('label')))}</div>" for col in columns)
    instruction_cells = "".join(_render_trajectory_instruction_cell(col) for col in columns)
    top_cells = "".join(_render_trajectory_cell(col.get("top", {}), row="top", column_id=str(col.get("id"))) for col in columns)
    bottom_cells = "".join(_render_trajectory_cell(col.get("bottom", {}), row="bottom", column_id=str(col.get("id"))) for col in columns)
    return f"""
<section class="trajectory-comparison" data-trajectory-comparison>
<h2>Trajectory Comparison</h2>
<p class="trajectory-help">Top row shows the seed/gold trajectory; bottom row shows the agent-produced outputs. Select a preview cell, then use the buttons or keyboard arrow keys to move through its pages.</p>
<div class="trajectory-controls" aria-label="Selected artifact page controls">
<button type="button" id="trajectory-prev" data-trajectory-prev disabled>← Previous page</button>
<span id="trajectory-selection-status" data-trajectory-selection-status>Select a preview cell</span>
<button type="button" id="trajectory-next" data-trajectory-next disabled>Next page →</button>
</div>
<div class="trajectory-scroll">
<div class="trajectory-grid" style="--trajectory-columns: {len(columns)};" data-trajectory-grid>
<div class="trajectory-corner" aria-hidden="true"></div>{headers}
<div class="trajectory-row-label">Instruction</div>{instruction_cells}
<div class="trajectory-row-label">Seed / gold</div>{top_cells}
<div class="trajectory-row-label">Agent output</div>{bottom_cells}
</div>
</div>
</section>
"""


def write_review_html(report_data: dict[str, Any], workspace: RunWorkspace) -> Path:
    path = workspace.review_dir / "index.html"
    summary = report_data["summary"]
    distribution = report_data.get("point_distribution", {})
    check_rows = "".join(
        "<tr>"
        f"<td>{html.escape(c['turn_id'])}</td><td>{html.escape(c['check_id'])}</td><td>{html.escape(c['evaluator'])}</td>"
        f"<td class='{html.escape(c['status'])}'>{html.escape(c['status'])}</td><td>{c['earned_points']:.2f}/{c['points']:.2f}</td>"
        f"<td>{html.escape(c['message'])}</td>"
        "</tr>"
        for c in report_data["checks"]
    )
    trajectory_html = _render_trajectory_comparison(report_data)
    legacy_html = _render_legacy_asset_cards(report_data)
    html_text = f"""<!doctype html>
<meta charset="utf-8">
<title>CUIF Review: {html.escape(report_data['task']['title'])}</title>
<style>
:root {{ color-scheme: light; --border: #ccd5e0; --muted: #5f6b7a; --accent: #1f6feb; --accent-soft: #e8f1ff; --warn-soft: #fff6d8; --error-soft: #fff0f3; }}
body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; color: #172033; background: #f7f9fc; }}
h1 {{ margin-bottom: 1rem; }}
.summary {{ padding: 1rem; background: #eef5ff; border: 1px solid #d6e7ff; border-radius: 12px; }}
.trajectory-comparison {{ margin-top: 1.5rem; }}
.trajectory-help {{ color: var(--muted); max-width: 76rem; }}
.trajectory-controls {{ position: sticky; top: 0; z-index: 2; display: flex; gap: .75rem; align-items: center; flex-wrap: wrap; margin: 1rem 0; padding: .75rem; background: rgba(247, 249, 252, .94); backdrop-filter: blur(6px); border: 1px solid var(--border); border-radius: 12px; }}
.trajectory-controls button {{ border: 1px solid #b6c7da; border-radius: 999px; padding: .45rem .8rem; background: white; color: #172033; cursor: pointer; }}
.trajectory-controls button:disabled {{ opacity: .45; cursor: not-allowed; }}
.trajectory-controls button:not(:disabled):hover {{ border-color: var(--accent); color: var(--accent); }}
#trajectory-selection-status {{ color: var(--muted); font-size: .95rem; }}
.trajectory-scroll {{ overflow-x: auto; padding-bottom: .5rem; }}
.trajectory-grid {{ display: grid; grid-template-columns: minmax(7rem, .45fr) repeat(var(--trajectory-columns), minmax(240px, 1fr)); gap: .75rem; align-items: stretch; }}
.trajectory-corner, .trajectory-column-header, .trajectory-row-label {{ border: 1px solid var(--border); border-radius: 10px; background: #f0f4fa; padding: .75rem; font-weight: 700; }}
.trajectory-column-header {{ text-align: center; }}
.trajectory-row-label {{ display: flex; align-items: center; justify-content: center; color: #314157; writing-mode: horizontal-tb; }}
.trajectory-instruction-cell {{ min-width: 0; max-height: 12rem; overflow-y: auto; overflow-wrap: anywhere; border: 1px solid var(--border); border-radius: 12px; padding: .75rem; background: #fffdf7; color: #28364a; font-size: .86rem; line-height: 1.38; white-space: normal; }}
.trajectory-instruction-cell--empty {{ display: flex; align-items: center; justify-content: center; color: var(--muted); font-style: italic; background: #fbfcfe; }}
.trajectory-cell {{ min-width: 0; min-height: 260px; border: 1px solid var(--border); border-radius: 14px; padding: .75rem; background: white; box-shadow: 0 1px 2px rgba(23, 32, 51, .04); outline: none; transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease; }}
.trajectory-cell--selectable {{ cursor: pointer; }}
.trajectory-cell--selectable:hover, .trajectory-cell--selectable:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft), 0 6px 18px rgba(23, 32, 51, .08); transform: translateY(-1px); }}
.trajectory-cell--selected {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft), 0 10px 24px rgba(23, 32, 51, .12); }}
.trajectory-cell--missing, .trajectory-cell--not_produced, .trajectory-cell--placeholder, .trajectory-cell--error {{ background: repeating-linear-gradient(-45deg, #fff, #fff 10px, #fbfcff 10px, #fbfcff 20px); }}
.trajectory-cell--not_produced {{ background-color: var(--warn-soft); }}
.trajectory-cell--missing, .trajectory-cell--error {{ background-color: var(--error-soft); }}
.trajectory-cell-header {{ display: flex; align-items: start; justify-content: space-between; gap: .75rem; margin-bottom: .4rem; }}
.trajectory-status {{ flex: none; border-radius: 999px; background: #edf2f7; color: #435268; padding: .12rem .5rem; font-size: .76rem; font-weight: 700; text-transform: uppercase; }}
.trajectory-artifact {{ display: flex; align-items: center; justify-content: space-between; gap: .5rem; color: var(--muted); font-size: .82rem; margin-bottom: .6rem; }}
.trajectory-artifact code {{ overflow-wrap: anywhere; }}
.trajectory-preview {{ display: flex; align-items: center; justify-content: center; min-height: 168px; border: 1px solid #e0e5ed; border-radius: 10px; background: #fbfcfe; overflow: hidden; }}
.trajectory-preview-image {{ max-width: 100%; max-height: 230px; border: 0; display: block; }}
.trajectory-preview-frame {{ width: 100%; min-height: 210px; border: 0; background: white; }}
.trajectory-missing-message {{ padding: 1rem; color: #6f4e00; text-align: center; font-weight: 650; }}
.trajectory-page-indicator {{ margin-top: .55rem; text-align: right; color: var(--muted); font-size: .82rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
.asset {{ border: 1px solid var(--border); border-radius: 8px; padding: 1rem; background: #fff; }}
.asset img {{ max-width: 100%; border: 1px solid #ddd; }}
.asset iframe {{ width: 100%; min-height: 240px; border: 1px solid #ddd; }}
.legacy-comparison {{ margin-top: 1rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; background: white; }}
th, td {{ border: 1px solid #ddd; padding: .4rem; vertical-align: top; }}
.pass {{ color: #087f23; font-weight: 700; }} .fail, .error {{ color: #b00020; font-weight: 700; }} .blocked {{ color: #9a6700; font-weight: 700; }} .skipped {{ color: #5f6368; }}
</style>
<h1>CUIF Human Review</h1>
<div class="summary"><strong>Score:</strong> {summary['earned_points']:.2f} / {summary['possible_points']:.2f} ({summary['final_score']:.1%})<br><strong>Status counts:</strong> {html.escape(str(summary['status_counts']))}<br><strong>Thesis-heavy point share:</strong> {html.escape(f"{distribution.get('thesis_heavy_points', 0.0):.2f} / {distribution.get('review_points', 0.0):.2f} ({distribution.get('thesis_heavy_share', 0.0):.1%})")}</div>
{trajectory_html}
{legacy_html}
<h2>Check Results</h2>
<table><thead><tr><th>Turn</th><th>Check</th><th>Evaluator</th><th>Status</th><th>Points</th><th>Message</th></tr></thead><tbody>{check_rows}</tbody></table>
<script>
(function () {{
  const root = document.querySelector('[data-trajectory-comparison]');
  if (!root) return;
  const cells = Array.from(root.querySelectorAll('[data-trajectory-cell][data-selectable="true"]'));
  const prev = root.querySelector('[data-trajectory-prev]');
  const next = root.querySelector('[data-trajectory-next]');
  const status = root.querySelector('[data-trajectory-selection-status]');
  let selected = null;

  function imagesFor(cell) {{
    try {{ return JSON.parse(cell.dataset.images || '[]'); }} catch (_) {{ return []; }}
  }}

  function currentIndex(cell) {{
    return Number.parseInt(cell.dataset.currentIndex || '0', 10) || 0;
  }}

  function setControls() {{
    if (!selected) {{
      prev.disabled = true;
      next.disabled = true;
      status.textContent = 'Select a preview cell';
      return;
    }}
    const images = imagesFor(selected);
    const index = currentIndex(selected);
    prev.disabled = images.length < 2 || index <= 0;
    next.disabled = images.length < 2 || index >= images.length - 1;
    const label = selected.querySelector('.trajectory-cell-header strong')?.textContent || 'Selected cell';
    status.textContent = images.length ? `${{label}} — page ${{index + 1}} of ${{images.length}}` : `${{label}} — summary preview`;
  }}

  function show(cell, index) {{
    const images = imagesFor(cell);
    if (!images.length) {{ setControls(); return; }}
    const bounded = Math.max(0, Math.min(index, images.length - 1));
    cell.dataset.currentIndex = String(bounded);
    const image = cell.querySelector('.trajectory-preview-image');
    if (image) image.src = images[bounded];
    const indicator = cell.querySelector('[data-page-indicator]');
    if (indicator) indicator.textContent = `${{bounded + 1}} / ${{images.length}}`;
    setControls();
  }}

  function select(cell) {{
    if (!cell || cell.dataset.selectable !== 'true') return;
    if (selected) selected.classList.remove('trajectory-cell--selected');
    selected = cell;
    selected.classList.add('trajectory-cell--selected');
    show(selected, currentIndex(selected));
  }}

  cells.forEach((cell) => {{
    cell.addEventListener('click', () => select(cell));
    cell.addEventListener('focus', () => select(cell));
    cell.addEventListener('keydown', (event) => {{
      if (event.key === 'Enter' || event.key === ' ') {{ event.preventDefault(); select(cell); }}
    }});
  }});

  prev.addEventListener('click', () => {{ if (selected) show(selected, currentIndex(selected) - 1); }});
  next.addEventListener('click', () => {{ if (selected) show(selected, currentIndex(selected) + 1); }});
  document.addEventListener('keydown', (event) => {{
    if (!selected) return;
    if (event.key === 'ArrowLeft') {{ event.preventDefault(); show(selected, currentIndex(selected) - 1); }}
    if (event.key === 'ArrowRight') {{ event.preventDefault(); show(selected, currentIndex(selected) + 1); }}
  }});
  if (cells.length) select(cells[0]);
}})();
</script>
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
