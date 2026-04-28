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


ALWAYS_EXPOSED_ROLES = {"seed"}
OPTIONAL_EXPOSED_ROLES = {"source_reference"}
TURN_INPUT_CATEGORIES = ("textual", "visual")


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


def _package_ref_name(ref: str) -> str:
    return ref.split(".", 1)[1]


def _format_file_entry(artifact: dict[str, str]) -> str:
    detail = artifact["role"]
    if artifact.get("category"):
        detail = f"{detail}, {artifact['category']}"
    return f"- `{artifact['workspace_path']}` ({detail})"


def _format_turn_instruction(
    manifest: Manifest,
    turn: TurnSpec,
    *,
    previous_turn: TurnSpec | None,
    new_input_files: list[dict[str, str]],
    available_files: list[dict[str, str]],
) -> str:
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
    if new_input_files:
        lines.extend(["New input files revealed for this turn:", ""])
        for category in TURN_INPUT_CATEGORIES:
            categorized = [artifact for artifact in new_input_files if artifact["category"] == category]
            if not categorized:
                continue
            lines.append(f"{category.title()} inputs:")
            for artifact in categorized:
                lines.append(_format_file_entry(artifact))
            lines.append("")
    else:
        lines.extend(["No new textual or visual input files are revealed in this turn.", ""])
    if available_files:
        lines.extend(["Currently available task files:", ""])
        for artifact in available_files:
            lines.append(_format_file_entry(artifact))
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
    controller_inputs_dir = controller_dir / "inputs"
    outputs_dir = current_dir / "outputs"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    controller_inputs_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    exposed_roles = set(ALWAYS_EXPOSED_ROLES)
    if include_source_references:
        exposed_roles.update(OPTIONAL_EXPOSED_ROLES)

    staged_input_refs = {ref for turn in manifest.turns for ref in turn.new_inputs.refs()}

    used_names: set[str] = set()
    always_exposed_files: list[dict[str, str]] = []
    hidden_artifacts: list[dict[str, str]] = []
    for artifact_name, spec in manifest.package_artifacts.items():
        role = str(spec.get("role", ""))
        source = safe_join(manifest.task_dir, spec["path"])
        if role not in exposed_roles:
            artifact_ref = f"package.{artifact_name}"
            if artifact_ref not in staged_input_refs:
                hidden_artifacts.append({"name": artifact_name, "role": role, "path": spec["path"]})
            continue
        destination_name = _artifact_destination_name(artifact_name, source, used_names)
        destination = current_dir / destination_name
        _copy_file(source, destination)
        always_exposed_files.append(
            {
                "name": artifact_name,
                "role": role,
                "source_path": spec["path"],
                "workspace_path": destination_name,
                "type": str(spec.get("type", "")),
                "category": "",
            }
        )

    turn_inputs: dict[str, list[dict[str, str]]] = {}
    for turn in manifest.turns:
        turn_used_names: set[str] = set()
        turn_records: list[dict[str, str]] = []
        for category in TURN_INPUT_CATEGORIES:
            for artifact_ref in getattr(turn.new_inputs, category):
                artifact_name = _package_ref_name(artifact_ref)
                spec = manifest.package_artifacts[artifact_name]
                source = safe_join(manifest.task_dir, spec["path"])
                destination_name = _artifact_destination_name(artifact_name, source, turn_used_names)
                turn_records.append(
                    {
                        "name": artifact_name,
                        "role": str(spec.get("role", "")),
                        "source_path": str(spec["path"]),
                        "controller_path": f".cuif_bundle/inputs/{turn.id}/{destination_name}",
                        "workspace_path": f"inputs/{turn.id}/{destination_name}",
                        "type": str(spec.get("type", "")),
                        "category": category,
                    }
                )
                _copy_file(source, controller_inputs_dir / turn.id / destination_name)
        turn_inputs[turn.id] = turn_records

    output_paths: list[dict[str, str]] = []
    for turn in manifest.turns:
        output_path = _turn_output_path(manifest, turn)
        safe_join(current_dir, output_path).parent.mkdir(parents=True, exist_ok=True)
        output_paths.append({"turn": turn.id, "output": turn.expected_output, "path": output_path})

    previous_turn: TurnSpec | None = None
    available_files = list(always_exposed_files)
    for turn in manifest.turns:
        new_input_files = turn_inputs[turn.id]
        text = _format_turn_instruction(
            manifest,
            turn,
            previous_turn=previous_turn,
            new_input_files=new_input_files,
            available_files=[*available_files, *new_input_files],
        )
        (instructions_dir / f"{turn.id}.md").write_text(text, encoding="utf-8")
        available_files.extend(new_input_files)
        previous_turn = turn

    first_turn = manifest.turns[0]
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
        "bundle_version": 2,
        "task_id": manifest.id,
        "task_title": manifest.title,
        "source_task_dir": str(manifest.task_dir),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "agent_workspace": "current",
        "active_turn": None,
        "exposed_roles": sorted(exposed_roles),
        "always_exposed_files": always_exposed_files,
        "exposed_files": list(always_exposed_files),
        "hidden_artifacts": hidden_artifacts,
        "staged_turns": [],
        "turn_inputs": turn_inputs,
        "turns": [{"id": turn.id, "instruction": f".cuif_bundle/instructions/{turn.id}.md"} for turn in manifest.turns],
        "outputs": output_paths,
    }
    (controller_dir / "bundle_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    stage_result = stage_bundle_turn(out_dir, first_turn.id)
    metadata = stage_result["metadata"]
    (out_dir / "README.md").write_text(_bundle_readme(manifest, metadata), encoding="utf-8")
    return {"manifest": manifest, "bundle_dir": out_dir, "current_dir": current_dir, "metadata": metadata}


def _bundle_root(bundle_dir: str | Path) -> Path:
    path = Path(bundle_dir).resolve()
    if (path / ".cuif_bundle" / "bundle_metadata.json").exists():
        return path
    if (path.parent / ".cuif_bundle" / "bundle_metadata.json").exists() and path.name == "current":
        return path.parent
    raise FileNotFoundError(f"bundle metadata not found under bundle root or current/ workspace: {path}")


def _refresh_exposed_files(metadata: dict[str, Any]) -> None:
    staged_turns = metadata.get("staged_turns", [])
    exposed_files = list(metadata.get("always_exposed_files", []))
    turn_inputs = metadata.get("turn_inputs", {})
    for turn_id in staged_turns:
        exposed_files.extend(turn_inputs.get(turn_id, []))
    metadata["exposed_files"] = exposed_files


def stage_bundle_turn(bundle_dir: str | Path, turn_id: str) -> dict[str, Any]:
    """Reveal one turn's instruction and newly declared inputs in ``current/``."""
    root = _bundle_root(bundle_dir)
    metadata_path = root / ".cuif_bundle" / "bundle_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    turn_ids = [turn["id"] for turn in metadata.get("turns", [])]
    if turn_id not in turn_ids:
        raise ValueError(f"unknown bundle turn: {turn_id}")

    staged_turns = list(metadata.get("staged_turns", []))
    target_index = turn_ids.index(turn_id)
    missing_previous = [previous for previous in turn_ids[:target_index] if previous not in staged_turns]
    if missing_previous:
        raise ValueError(f"stage previous turns first before {turn_id}: {', '.join(missing_previous)}")

    current_dir = safe_join(root, metadata.get("agent_workspace", "current"))
    instruction_src = safe_join(root, f".cuif_bundle/instructions/{turn_id}.md")
    instruction_dst = current_dir / "instruction.md"
    _copy_file(instruction_src, instruction_dst)

    copied_inputs: list[dict[str, str]] = []
    for artifact in metadata.get("turn_inputs", {}).get(turn_id, []):
        if artifact.get("controller_path"):
            source = safe_join(root, artifact["controller_path"])
        else:
            source_task_dir = Path(metadata["source_task_dir"]).resolve()
            source = safe_join(source_task_dir, artifact["source_path"])
        destination = safe_join(current_dir, artifact["workspace_path"])
        _copy_file(source, destination)
        copied_inputs.append(artifact)

    if turn_id not in staged_turns:
        staged_turns.append(turn_id)
    metadata["active_turn"] = turn_id
    metadata["staged_turns"] = staged_turns
    metadata["last_staged_at"] = datetime.now(timezone.utc).isoformat()
    _refresh_exposed_files(metadata)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return {"bundle_dir": root, "current_dir": current_dir, "turn": turn_id, "copied_inputs": copied_inputs, "metadata": metadata}


def _bundle_readme(manifest: Manifest, metadata: dict[str, Any]) -> str:
    output_lines = "\n".join(f"- `{item['path']}`" for item in metadata["outputs"])
    turn_lines = "\n".join(f"- `{turn['id']}`: `{turn['instruction']}`" for turn in metadata["turns"])
    stage_lines = "\n".join(
        [
            "uv run cuif-eval stage-bundle-turn \\",
            "  --bundle . \\",
            "  --turn <next_turn_id>",
        ]
    )
    return "\n".join(
        [
            f"# CUIF external-agent bundle: {manifest.id}",
            "",
            "Open only `current/` as the evaluated agent workspace.",
            "",
            "The controller files under `.cuif_bundle/` are for the benchmark operator. Do not expose them to the evaluated agent if future-turn instructions or inputs should remain hidden.",
            "",
            "To stage the next turn in the same agent workspace, run the staging command from this bundle root. It updates `current/instruction.md` and copies only that turn's newly revealed input files into `current/inputs/<turn>/`.",
            "",
            "```bash",
            stage_lines,
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
