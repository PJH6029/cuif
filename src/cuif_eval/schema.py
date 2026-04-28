from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .types import CheckSpec, Manifest, TurnInputSpec, TurnSpec

KNOWN_EVALUATORS = {
    "file_exists",
    "pptx_slide_count",
    "pptx_text_contains",
    "pptx_bbox_region",
    "pptx_style_check",
    "pptx_chart_data",
    "pptx_image_count",
    "pptx_image_match",
    "pptx_formula_present",
    "pptx_preservation_diff",
    "rendered_layout_review",
    "rendered_image_similarity",
    "llm_text_rubric",
    "vlm_layout_rubric",
}
JUDGE_EVALUATORS = {"llm_text_rubric", "vlm_layout_rubric"}
PPTX_EVALUATORS = {
    "pptx_slide_count",
    "pptx_text_contains",
    "pptx_bbox_region",
    "pptx_style_check",
    "pptx_chart_data",
    "pptx_image_count",
    "pptx_image_match",
    "pptx_formula_present",
    "pptx_preservation_diff",
    "rendered_layout_review",
    "rendered_image_similarity",
    "vlm_layout_rubric",
}
GENERATED_ARTIFACT_PATH_PREFIXES = ("run/", "outputs/", "previews/", "review/", "reports/", "output/")
GENERATED_ARTIFACT_FILENAMES = {"report.json", "report.md", "index.html"}
AGENT_INPUT_ROLES = {"source_input", "instruction_input", "style_input"}
TURN_INPUT_KEYS = ("textual", "visual")
TURN_INPUT_TYPES = {
    "textual": {"txt", "json", "xlsx", "docx", "pdf"},
    "visual": {"image", "svg", "png"},
}


class ManifestValidationError(ValueError):
    """Raised when a manifest violates the CUIF author/evaluator boundary."""

    def __init__(self, errors: list[str]):
        super().__init__("Manifest validation failed:\n- " + "\n- ".join(errors))
        self.errors = errors


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ManifestValidationError(["manifest root must be a mapping"])
    return data


def _safe_relative_path(value: Any, *, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field} must be a non-empty relative path")
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{field} rejects absolute/path-traversal path: {value}")
        return None
    return path


def _artifact_type_for_ref(ref: str, package_artifacts: dict[str, dict[str, Any]], expected_outputs: dict[str, dict[str, dict[str, Any]]]) -> str | None:
    parts = ref.split(".")
    if len(parts) == 2 and parts[0] == "package":
        artifact = package_artifacts.get(parts[1])
        return str(artifact.get("type")) if artifact else None
    if len(parts) == 4 and parts[:2] == ["run", "outputs"]:
        output = expected_outputs.get(parts[2], {}).get(parts[3])
        return str(output.get("type")) if output else None
    return None


def _validate_artifact_ref(ref: Any, package_artifacts: dict[str, dict[str, Any]], expected_outputs: dict[str, dict[str, dict[str, Any]]], errors: list[str], *, field: str) -> None:
    if not isinstance(ref, str):
        errors.append(f"{field} must be an artifact reference string")
        return
    parts = ref.split(".")
    if len(parts) == 2 and parts[0] == "package" and parts[1] in package_artifacts:
        return
    if len(parts) == 4 and parts[:2] == ["run", "outputs"] and parts[2] in expected_outputs and parts[3] in expected_outputs[parts[2]]:
        return
    errors.append(f"{field} references unknown artifact namespace: {ref}")


def _validate_turn_new_inputs(turn_id: str, raw: Any, package_artifacts: dict[str, dict[str, Any]], errors: list[str]) -> TurnInputSpec:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        errors.append(f"turn {turn_id} new_inputs must be a mapping with textual/visual lists")
        raw = {}

    for key in raw:
        if key not in TURN_INPUT_KEYS:
            errors.append(f"turn {turn_id} new_inputs has unsupported category: {key}")

    values: dict[str, list[str]] = {"textual": [], "visual": []}
    seen_local: set[str] = set()
    for category in TURN_INPUT_KEYS:
        refs = raw.get(category, [])
        if refs is None:
            refs = []
        if not isinstance(refs, list):
            errors.append(f"turn {turn_id} new_inputs.{category} must be a list of package artifact refs")
            refs = []
        for index, ref in enumerate(refs):
            field = f"turn {turn_id} new_inputs.{category}[{index}]"
            if not isinstance(ref, str):
                errors.append(f"{field} must be a package artifact reference string")
                continue
            parts = ref.split(".")
            if len(parts) != 2 or parts[0] != "package" or parts[1] not in package_artifacts:
                errors.append(f"{field} references unknown package artifact: {ref}")
                continue
            if ref in seen_local:
                errors.append(f"turn {turn_id} new_inputs repeats {ref}")
                continue
            seen_local.add(ref)

            artifact_name = parts[1]
            spec = package_artifacts[artifact_name]
            role = str(spec.get("role", ""))
            artifact_type = str(spec.get("type", ""))
            if role not in AGENT_INPUT_ROLES:
                errors.append(f"{field} references package.{artifact_name} with non-agent-input role: {role}")
            if artifact_type not in TURN_INPUT_TYPES[category]:
                errors.append(f"{field} has type {artifact_type!r}, which is not supported for {category} inputs")
            values[category].append(ref)

    return TurnInputSpec(textual=values["textual"], visual=values["visual"])


def load_manifest(path: str | Path, *, skip_judges: bool = False, validate_files: bool = True) -> Manifest:
    manifest_path = Path(path).resolve()
    if manifest_path.is_dir():
        manifest_path = manifest_path / "manifest.yaml"
    raw = _load_mapping(manifest_path)
    task_dir = manifest_path.parent
    errors: list[str] = []

    for key in ("manifest_version", "id", "title", "primary_artifact_family", "artifact_families", "tracks", "artifacts", "turns"):
        if key not in raw:
            errors.append(f"missing required top-level field: {key}")

    artifacts = raw.get("artifacts", {}) if isinstance(raw.get("artifacts", {}), dict) else {}
    package_artifacts = artifacts.get("package", {}) if isinstance(artifacts.get("package", {}), dict) else {}
    expected_outputs = artifacts.get("expected_outputs", {}) if isinstance(artifacts.get("expected_outputs", {}), dict) else {}
    if not package_artifacts:
        errors.append("artifacts.package must declare immutable task-package artifacts")
    if not expected_outputs:
        errors.append("artifacts.expected_outputs must declare adapter-produced outputs")

    for name, spec in package_artifacts.items():
        if not isinstance(spec, dict):
            errors.append(f"package artifact {name} must be a mapping")
            continue
        rel = _safe_relative_path(spec.get("path"), field=f"artifacts.package.{name}.path", errors=errors)
        if spec.get("type") not in {"pptx", "docx", "xlsx", "pdf", "image", "svg", "png", "json", "txt"}:
            errors.append(f"artifacts.package.{name}.type is unsupported or missing: {spec.get('type')}")
        if rel is not None:
            posix = rel.as_posix()
            if posix in GENERATED_ARTIFACT_FILENAMES or posix.startswith(GENERATED_ARTIFACT_PATH_PREFIXES):
                errors.append(f"artifacts.package.{name}.path points at generated evaluator output: {posix}")
            if validate_files and not (task_dir / rel).exists():
                errors.append(f"package artifact {name} is missing: {rel}")

    normalized_outputs: dict[str, dict[str, dict[str, Any]]] = {}
    for turn_id, outputs in expected_outputs.items():
        if not isinstance(outputs, dict):
            errors.append(f"expected_outputs.{turn_id} must be a mapping")
            continue
        normalized_outputs[turn_id] = {}
        for output_id, spec in outputs.items():
            if not isinstance(spec, dict):
                errors.append(f"expected_outputs.{turn_id}.{output_id} must be a mapping")
                continue
            _safe_relative_path(spec.get("path"), field=f"expected_outputs.{turn_id}.{output_id}.path", errors=errors)
            if spec.get("type") not in {"pptx", "docx", "xlsx", "image", "json", "txt"}:
                errors.append(f"expected_outputs.{turn_id}.{output_id}.type is unsupported or missing: {spec.get('type')}")
            normalized_outputs[turn_id][output_id] = spec

    turns_raw = raw.get("turns", [])
    if not isinstance(turns_raw, list) or not turns_raw:
        errors.append("turns must be a non-empty list")
        turns_raw = []
    seen_turns: set[str] = set()
    seen_checks: set[str] = set()
    assigned_new_inputs: dict[str, tuple[str, str]] = {}
    all_dependencies: dict[str, list[str]] = {}
    turns: list[TurnSpec] = []
    judge_config = raw.get("judge", {}) if isinstance(raw.get("judge", {}), dict) else {}

    for idx, turn in enumerate(turns_raw):
        if not isinstance(turn, dict):
            errors.append(f"turns[{idx}] must be a mapping")
            continue
        turn_id = str(turn.get("id", ""))
        if not turn_id:
            errors.append(f"turns[{idx}].id is required")
        elif turn_id in seen_turns:
            errors.append(f"duplicate turn id: {turn_id}")
        seen_turns.add(turn_id)
        expected_output = str(turn.get("expected_output", ""))
        if not expected_output:
            errors.append(f"turn {turn_id} missing expected_output")
        elif turn_id not in normalized_outputs or expected_output not in normalized_outputs.get(turn_id, {}):
            errors.append(f"turn {turn_id} expected_output {expected_output!r} is not declared in artifacts.expected_outputs")
        new_inputs = _validate_turn_new_inputs(turn_id or f"turns[{idx}]", turn.get("new_inputs", {}), package_artifacts, errors)
        for category in TURN_INPUT_KEYS:
            for ref in getattr(new_inputs, category):
                previous = assigned_new_inputs.get(ref)
                if previous is not None:
                    errors.append(f"{ref} is newly revealed more than once: {previous[0]}.new_inputs.{previous[1]} and {turn_id}.new_inputs.{category}")
                else:
                    assigned_new_inputs[ref] = (turn_id, category)
        checks_raw = turn.get("checks", [])
        if not isinstance(checks_raw, list):
            errors.append(f"turn {turn_id} checks must be a list")
            checks_raw = []
        check_specs: list[CheckSpec] = []
        for cidx, check in enumerate(checks_raw):
            if not isinstance(check, dict):
                errors.append(f"turn {turn_id} check {cidx} must be a mapping")
                continue
            check_id = str(check.get("id", ""))
            evaluator = str(check.get("evaluator", ""))
            artifact = check.get("artifact")
            if not check_id:
                errors.append(f"turn {turn_id} check {cidx} missing id")
            elif check_id in seen_checks:
                errors.append(f"duplicate check id: {check_id}")
            seen_checks.add(check_id)
            if evaluator not in KNOWN_EVALUATORS:
                errors.append(f"unknown evaluator for check {check_id}: {evaluator}")
            _validate_artifact_ref(artifact, package_artifacts, normalized_outputs, errors, field=f"check {check_id}.artifact")
            artifact_type = _artifact_type_for_ref(str(artifact), package_artifacts, normalized_outputs)
            if evaluator in PPTX_EVALUATORS and artifact_type is not None and artifact_type != "pptx":
                errors.append(f"check {check_id} uses PPTX evaluator {evaluator} on {artifact_type} artifact")
            points = check.get("points")
            if not isinstance(points, (int, float)) or isinstance(points, bool) or float(points) < 0:
                errors.append(f"check {check_id} points must be a non-negative number")
                points_value = 0.0
            else:
                points_value = float(points)
            params = check.get("params", {})
            if not isinstance(params, dict):
                errors.append(f"check {check_id} params must be a mapping")
                params = {}
            depends_on = check.get("depends_on", [])
            if depends_on is None:
                depends_on = []
            if not isinstance(depends_on, list) or not all(isinstance(dep, str) for dep in depends_on):
                errors.append(f"check {check_id} depends_on must be a list of check ids")
                depends_on = []
            all_dependencies[check_id] = list(depends_on)
            optional = bool(check.get("optional", False))
            diagnostic = bool(check.get("diagnostic", False))
            if evaluator in JUDGE_EVALUATORS:
                prompt = params.get("prompt")
                rubric = params.get("rubric")
                model = params.get("model") or judge_config.get("model")
                base_url = params.get("base_url") or judge_config.get("base_url")
                if not prompt or not rubric:
                    errors.append(f"judge check {check_id} must declare prompt and rubric")
                if not skip_judges and not optional and (not model or not base_url):
                    errors.append(f"judge check {check_id} needs model/base_url unless skipped or optional")
            check_specs.append(
                CheckSpec(
                    id=check_id,
                    evaluator=evaluator,
                    artifact=str(artifact),
                    points=points_value,
                    params=params,
                    depends_on=list(depends_on),
                    optional=optional,
                    diagnostic=diagnostic,
                    description=check.get("description"),
                )
            )
        turns.append(TurnSpec(id=turn_id, instruction=str(turn.get("instruction", "")), expected_output=expected_output, checks=check_specs, new_inputs=new_inputs))

    unknown_deps = sorted({dep for deps in all_dependencies.values() for dep in deps if dep not in seen_checks})
    for dep in unknown_deps:
        errors.append(f"dependency references unknown check id: {dep}")

    assigned_refs = set(assigned_new_inputs)
    for artifact_name, spec in package_artifacts.items():
        role = str(spec.get("role", ""))
        if role in AGENT_INPUT_ROLES:
            ref = f"package.{artifact_name}"
            if ref not in assigned_refs:
                errors.append(f"agent-facing package artifact {ref} with role {role} must be listed once under turns[].new_inputs.textual or turns[].new_inputs.visual")

    if errors:
        raise ManifestValidationError(errors)

    return Manifest(
        path=manifest_path,
        task_dir=task_dir,
        raw=raw,
        manifest_version=str(raw["manifest_version"]),
        id=str(raw["id"]),
        title=str(raw["title"]),
        primary_artifact_family=str(raw["primary_artifact_family"]),
        artifact_families=[str(x) for x in raw.get("artifact_families", [])],
        tracks=[str(x) for x in raw.get("tracks", [])],
        package_artifacts=package_artifacts,
        expected_outputs=normalized_outputs,
        turns=turns,
        review=raw.get("review", {}) if isinstance(raw.get("review", {}), dict) else {},
        scoring=raw.get("scoring", {}) if isinstance(raw.get("scoring", {}), dict) else {},
        judge=judge_config,
    )


def validate_manifest(path: str | Path, *, skip_judges: bool = False) -> Manifest:
    return load_manifest(path, skip_judges=skip_judges)
