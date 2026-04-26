from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import ManifestValidationError
from .types import Manifest


class ArtifactResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class RunWorkspace:
    task_dir: Path
    run_dir: Path
    task_copy_dir: Path
    work_dir: Path
    outputs_dir: Path
    previews_dir: Path
    judge_cache_dir: Path
    review_dir: Path
    logs_dir: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "task_dir": str(self.task_dir),
            "run_dir": str(self.run_dir),
            "task_copy_dir": str(self.task_copy_dir),
            "work_dir": str(self.work_dir),
            "outputs_dir": str(self.outputs_dir),
            "previews_dir": str(self.previews_dir),
            "judge_cache_dir": str(self.judge_cache_dir),
            "review_dir": str(self.review_dir),
            "logs_dir": str(self.logs_dir),
        }


def safe_join(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ArtifactResolutionError(f"unsafe path outside root: {relative}")
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ArtifactResolutionError(f"path traversal rejected: {relative}") from exc
    return path


def create_run_workspace(task_dir: str | Path, run_dir: str | Path, *, copy_task: bool = True, overwrite: bool = True) -> RunWorkspace:
    task_dir = Path(task_dir).resolve()
    run_dir = Path(run_dir).resolve()
    if run_dir.exists() and overwrite:
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
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
    for directory in (
        workspace.work_dir,
        workspace.outputs_dir,
        workspace.previews_dir,
        workspace.judge_cache_dir,
        workspace.review_dir,
        workspace.logs_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    if copy_task:
        if workspace.task_copy_dir.exists():
            shutil.rmtree(workspace.task_copy_dir)
        ignore = shutil.ignore_patterns("mock_outputs_broken", "__pycache__")
        shutil.copytree(task_dir, workspace.task_copy_dir, ignore=ignore)
    return workspace


def resolve_package_artifact(manifest: Manifest, artifact_name: str, workspace: RunWorkspace | None = None) -> Path:
    spec = manifest.package_artifacts.get(artifact_name)
    if spec is None:
        raise ArtifactResolutionError(f"unknown package artifact: {artifact_name}")
    if workspace is not None:
        run_local = safe_join(workspace.task_copy_dir, spec["path"])
        if run_local.exists():
            return run_local
    return safe_join(manifest.task_dir, spec["path"])


def resolve_run_output(manifest: Manifest, workspace: RunWorkspace, turn_id: str, output_name: str) -> Path:
    spec = manifest.expected_outputs.get(turn_id, {}).get(output_name)
    if spec is None:
        raise ArtifactResolutionError(f"unknown expected output: {turn_id}.{output_name}")
    return safe_join(workspace.outputs_dir / turn_id, spec["path"])


def resolve_artifact_ref(manifest: Manifest, workspace: RunWorkspace, artifact_ref: str) -> Path:
    parts = artifact_ref.split(".")
    if len(parts) == 2 and parts[0] == "package":
        return resolve_package_artifact(manifest, parts[1], workspace)
    if len(parts) == 4 and parts[:2] == ["run", "outputs"]:
        return resolve_run_output(manifest, workspace, parts[2], parts[3])
    raise ArtifactResolutionError(f"unsupported artifact reference: {artifact_ref}")


def output_reference(manifest: Manifest, workspace: RunWorkspace, artifact_ref: str) -> str:
    path = resolve_artifact_ref(manifest, workspace, artifact_ref)
    try:
        return path.relative_to(workspace.run_dir).as_posix()
    except ValueError:
        return path.as_posix()


def write_run_metadata(workspace: RunWorkspace, metadata: dict[str, Any]) -> Path:
    path = workspace.run_dir / "run_metadata.json"
    existing: dict[str, Any] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
    existing.update(metadata)
    path.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")
    return path


def read_run_metadata(run_dir: str | Path) -> dict[str, Any]:
    path = Path(run_dir) / "run_metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_task_dir(task_dir: str | Path) -> Path:
    task_dir = Path(task_dir).resolve()
    manifest = task_dir / "manifest.yaml"
    if not manifest.exists():
        raise ManifestValidationError([f"task directory missing manifest.yaml: {task_dir}"])
    return task_dir
