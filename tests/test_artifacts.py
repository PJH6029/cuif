from __future__ import annotations

import pytest

from cuif_eval.artifacts import ArtifactResolutionError, create_run_workspace, resolve_artifact_ref, safe_join
from cuif_eval.schema import ManifestValidationError, load_manifest


def test_task_package_and_run_output_paths_resolve(toy_task, tmp_path):
    manifest = load_manifest(toy_task / "manifest.yaml")
    workspace = create_run_workspace(toy_task, tmp_path / "run")
    seed = resolve_artifact_ref(manifest, workspace, "package.seed")
    assert seed.name == "seed.pptx"
    assert seed.is_relative_to(workspace.run_dir)
    assert resolve_artifact_ref(manifest, workspace, "run.outputs.turn1.result") == workspace.outputs_dir / "turn1" / "result.pptx"


def test_workspace_creation_creates_documented_directories(toy_task, tmp_path):
    workspace = create_run_workspace(toy_task, tmp_path / "run")
    for path in [workspace.task_copy_dir, workspace.work_dir, workspace.outputs_dir, workspace.previews_dir, workspace.judge_cache_dir, workspace.review_dir]:
        assert path.exists(), path


def test_path_traversal_is_rejected(tmp_path):
    with pytest.raises(ArtifactResolutionError):
        safe_join(tmp_path, "../outside")


def test_generated_report_paths_are_not_package_artifacts(mutate_manifest):
    path = mutate_manifest(lambda data: data["artifacts"]["package"]["seed"].update({"path": "report.json"}))
    with pytest.raises(ManifestValidationError, match="generated evaluator output"):
        load_manifest(path)
