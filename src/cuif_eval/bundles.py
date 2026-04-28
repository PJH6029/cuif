from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import create_run_workspace, safe_join, write_run_metadata
from .runner import evaluate_run
from .schema import load_manifest
from .scoring import aggregate_results
from .types import Manifest, TurnSpec


DEFAULT_EXPOSED_ROLES = {"seed", "source_input", "instruction_input", "style_input"}


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _artifact_destination_name(name: str, source: Path, used: set[str]) -> str:
    candidate = source.name
    if candidate not in used:
        used.add(candidate)
        return candidate
    stem = source.stem or name
    suffix = source.suffix
    candidate = f"{name}{suffix}" if suffix else name
    index = 2
    while candidate in used:
        candidate = f"{stem}_{index}{suffix}"
        index += 1
    used.add(candidate)
    return candidate


def _turn_output_path(manifest: Manifest, turn: TurnSpec) -> str:
    spec = manifest.expected_outputs[turn.id][turn.expected_output]
    return f"outputs/{turn.id}/{spec['path']}"


def _format_turn_instruction(manifest: Manifest, turn: TurnSpec, *, previous_turn: TurnSpec | None, exposed_files: list[dict[str, str]]) -> str:
    lines = [f"# {manifest.title} / {turn.id}", ""]
    if previous_turn is not None:
        lines.extend(
            [
                "Start from the previous turn output:",
                "",
                "```text",
                _turn_output_path(manifest, previous_turn),
                "```",
                "",
            ]
        )
    lines.extend([turn.instruction, ""])
    if exposed_files:
        lines.extend(["Available task files:", ""])
        for artifact in exposed_files:
            lines.append(f"- `{artifact['workspace_path']}` ({artifact['role']})")
        lines.append("")
    lines.extend(["Save the completed artifact exactly here:", "", "```text", _turn_output_path(manifest, turn), "```", ""])
    return "\n".join(lines)


def export_task_bundle(
    task_dir: str | Path,
    out_dir: str | Path,
    *,
    overwrite: bool = False,
    include_source_references: bool = False,
) -> dict[str, Any]:
    """Export a task-facing workspace for out-of-band agents.

    The generated bundle separates operator/controller files from the agent
    workspace. The evaluated agent should be pointed at ``current/`` only.
    """
    manifest = load_manifest(Path(task_dir) / "manifest.yaml", skip_judges=True)
    out_dir = Path(out_dir).resolve()
    if out_dir.exists():
        if not overwrite:
            raise FileExistsError(f"bundle directory already exists; pass --overwrite to replace it: {out_dir}")
        shutil.rmtree(out_dir)

    current_dir = out_dir / "current"
    controller_dir = out_dir / ".cuif_bundle"
    instructions_dir = controller_dir / "instructions"
    outputs_dir = current_dir / "outputs"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    exposed_roles = set(DEFAULT_EXPOSED_ROLES)
    if include_source_references:
        exposed_roles.add("source_reference")

    used_names: set[str] = set()
    exposed_files: list[dict[str, str]] = []
    hidden_artifacts: list[dict[str, str]] = []
    for artifact_name, spec in manifest.package_artifacts.items():
        role = str(spec.get("role", ""))
        source = safe_join(manifest.task_dir, spec["path"])
        if role not in exposed_roles:
            hidden_artifacts.append({"name": artifact_name, "role": role, "path": spec["path"]})
            continue
        destination_name = _artifact_destination_name(artifact_name, source, used_names)
        destination = current_dir / destination_name
        _copy_file(source, destination)
        exposed_files.append(
            {
                "name": artifact_name,
                "role": role,
                "source_path": spec["path"],
                "workspace_path": destination_name,
                "type": str(spec.get("type", "")),
            }
        )

    output_paths: list[dict[str, str]] = []
    for turn in manifest.turns:
        output_path = _turn_output_path(manifest, turn)
        safe_join(current_dir, output_path).parent.mkdir(parents=True, exist_ok=True)
        output_paths.append({"turn": turn.id, "output": turn.expected_output, "path": output_path})

    previous_turn: TurnSpec | None = None
    for turn in manifest.turns:
        text = _format_turn_instruction(manifest, turn, previous_turn=previous_turn, exposed_files=exposed_files)
        (instructions_dir / f"{turn.id}.md").write_text(text, encoding="utf-8")
        previous_turn = turn

    first_turn = manifest.turns[0]
    shutil.copy2(instructions_dir / f"{first_turn.id}.md", current_dir / "instruction.md")
    (current_dir / "AGENTS.md").write_text(
        "\n".join(
            [
                "# External CUIF Task Workspace",
                "",
                "You are solving a benchmark task in an isolated workspace.",
                "",
                "Rules:",
                "- Work only with files in this directory and its child directories.",
                "- Do not inspect parent directories or search for hidden evaluator files.",
                "- Follow `instruction.md` exactly.",
                "- Save the completed artifact to the exact output path specified in `instruction.md`.",
                "- Preserve protected content exactly when the instruction says to preserve it.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    metadata = {
        "bundle_version": 1,
        "task_id": manifest.id,
        "task_title": manifest.title,
        "source_task_dir": str(manifest.task_dir),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "agent_workspace": "current",
        "active_turn": first_turn.id,
        "exposed_roles": sorted(exposed_roles),
        "exposed_files": exposed_files,
        "hidden_artifacts": hidden_artifacts,
        "turns": [{"id": turn.id, "instruction": f".cuif_bundle/instructions/{turn.id}.md"} for turn in manifest.turns],
        "outputs": output_paths,
    }
    (controller_dir / "bundle_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "README.md").write_text(_bundle_readme(manifest, metadata), encoding="utf-8")
    return {"manifest": manifest, "bundle_dir": out_dir, "current_dir": current_dir, "metadata": metadata}


def _bundle_readme(manifest: Manifest, metadata: dict[str, Any]) -> str:
    output_lines = "\n".join(f"- `{item['path']}`" for item in metadata["outputs"])
    turn_lines = "\n".join(f"- `{turn['id']}`: `{turn['instruction']}`" for turn in metadata["turns"])
    return "\n".join(
        [
            f"# CUIF external-agent bundle: {manifest.id}",
            "",
            "Open only `current/` as the evaluated agent workspace.",
            "",
            "The controller files under `.cuif_bundle/` are for the benchmark operator. Do not expose them to the evaluated agent if future-turn instructions should remain hidden.",
            "",
            "To stage the next turn in the same agent workspace, copy the desired instruction file over `current/instruction.md`, for example:",
            "",
            "```bash",
            "cp .cuif_bundle/instructions/turn2.md current/instruction.md",
            "```",
            "",
            "Expected outputs:",
            "",
            output_lines,
            "",
            "Turn instruction files:",
            "",
            turn_lines,
            "",
        ]
    )


def _workspace_outputs_dir(workspace_dir: Path) -> Path:
    workspace_dir = workspace_dir.resolve()
    direct = workspace_dir / "outputs"
    nested = workspace_dir / "current" / "outputs"
    if direct.exists():
        return direct
    if nested.exists():
        return nested
    raise FileNotFoundError(f"workspace does not contain outputs/ or current/outputs/: {workspace_dir}")


def import_bundle_outputs(task_dir: str | Path, workspace_dir: str | Path, run_dir: str | Path, *, overwrite: bool = True) -> dict[str, Any]:
    manifest = load_manifest(Path(task_dir) / "manifest.yaml", skip_judges=True)
    workspace_dir = Path(workspace_dir).resolve()
    source_outputs_dir = _workspace_outputs_dir(workspace_dir)
    run_dir = Path(run_dir).resolve()
    if run_dir.exists() and not overwrite:
        raise FileExistsError(f"run directory already exists: {run_dir}")
    workspace = create_run_workspace(manifest.task_dir, run_dir, copy_task=True, overwrite=overwrite)

    copied: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for turn in manifest.turns:
        expected = manifest.expected_outputs.get(turn.id, {})
        for output_name, spec in expected.items():
            rel_path = Path(turn.id) / spec["path"]
            source = safe_join(source_outputs_dir, rel_path)
            destination = safe_join(workspace.outputs_dir, rel_path)
            if source.exists():
                _copy_file(source, destination)
                copied.append({"turn": turn.id, "output": output_name, "path": f"outputs/{rel_path.as_posix()}"})
            else:
                missing.append({"turn": turn.id, "output": output_name, "path": f"outputs/{rel_path.as_posix()}"})

    write_run_metadata(
        workspace,
        {
            "task_id": manifest.id,
            "task_dir": str(manifest.task_dir),
            "manifest_path": str(manifest.path),
            "adapter": "external_bundle",
            "adapter_status": "imported",
            "source_workspace": str(workspace_dir),
            "source_outputs_dir": str(source_outputs_dir),
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "imported_outputs": copied,
            "missing_outputs": missing,
            "workspace": workspace.as_dict(),
        },
    )
    return {"manifest": manifest, "workspace": workspace, "copied": copied, "missing": missing}


def evaluate_bundle_outputs(
    task_dir: str | Path,
    workspace_dir: str | Path,
    run_dir: str | Path,
    *,
    overwrite: bool = True,
    skip_judges: bool = False,
    judge_base_url: str | None = None,
    judge_model: str | None = None,
    judge_api_key_env: str = "OPENAI_API_KEY",
    judge_image_url_base: str | None = None,
    refresh_judge_cache: bool = False,
) -> dict[str, Any]:
    imported = import_bundle_outputs(task_dir, workspace_dir, run_dir, overwrite=overwrite)
    evaluated = evaluate_run(
        task_dir,
        imported["workspace"].run_dir,
        skip_judges=skip_judges,
        judge_base_url=judge_base_url,
        judge_model=judge_model,
        judge_api_key_env=judge_api_key_env,
        judge_image_url_base=judge_image_url_base,
        refresh_judge_cache=refresh_judge_cache,
    )
    summary = aggregate_results(evaluated["results"])
    return {**evaluated, "imported": imported, "summary": summary}
