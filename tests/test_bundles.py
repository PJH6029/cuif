from __future__ import annotations

import json
import shutil

from cuif_eval.bundles import evaluate_bundle_outputs, export_task_bundle
from cuif_eval.scoring import aggregate_results


def test_export_bundle_stages_agent_workspace_without_gold_or_manifest(toy_task, tmp_path):
    result = export_task_bundle(toy_task, tmp_path / "bundle")
    bundle = result["bundle_dir"]
    current = result["current_dir"]

    assert (current / "AGENTS.md").exists()
    assert (current / "instruction.md").read_text(encoding="utf-8").startswith("# Toy PPTX layout smoke task / turn1")
    assert (current / "seed.pptx").exists()
    assert (current / "sketch.svg").exists()
    assert (current / "outputs" / "turn1").is_dir()
    assert (current / "outputs" / "final").is_dir()
    assert not (current / "manifest.yaml").exists()
    assert not (current / "gold").exists()
    assert not list(current.rglob("*gold*"))

    metadata = json.loads((bundle / ".cuif_bundle" / "bundle_metadata.json").read_text(encoding="utf-8"))
    assert metadata["task_id"] == "toy_pptx_layout"
    assert metadata["active_turn"] == "turn1"
    assert [item["path"] for item in metadata["outputs"]] == ["outputs/turn1/result.pptx", "outputs/final/result.pptx"]
    assert (bundle / ".cuif_bundle" / "instructions" / "final.md").exists()
    assert "outputs/turn1/result.pptx" in (bundle / ".cuif_bundle" / "instructions" / "final.md").read_text(encoding="utf-8")


def test_export_bundle_refuses_to_overwrite_without_flag(toy_task, tmp_path):
    export_task_bundle(toy_task, tmp_path / "bundle")
    try:
        export_task_bundle(toy_task, tmp_path / "bundle")
    except FileExistsError as exc:
        assert "--overwrite" in str(exc)
    else:
        raise AssertionError("expected FileExistsError")


def test_evaluate_bundle_imports_outputs_and_generates_report(toy_task, tmp_path):
    bundle = export_task_bundle(toy_task, tmp_path / "bundle")["bundle_dir"]
    current = bundle / "current"
    shutil.copy2(toy_task / "mock_outputs" / "turn1" / "result.pptx", current / "outputs" / "turn1" / "result.pptx")
    shutil.copy2(toy_task / "mock_outputs" / "final" / "result.pptx", current / "outputs" / "final" / "result.pptx")

    result = evaluate_bundle_outputs(
        toy_task,
        current,
        tmp_path / "run",
        skip_judges=True,
    )
    run = result["workspace"].run_dir
    summary = aggregate_results(result["results"])

    assert (run / "outputs" / "turn1" / "result.pptx").exists()
    assert (run / "outputs" / "final" / "result.pptx").exists()
    assert (run / "report.md").exists()
    assert summary["final_score"] == 1.0
    metadata = json.loads((run / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["adapter"] == "external_bundle"
    assert metadata["adapter_status"] == "imported"
    assert metadata["missing_outputs"] == []


def test_evaluate_bundle_no_overwrite_refuses_existing_run(toy_task, tmp_path):
    bundle = export_task_bundle(toy_task, tmp_path / "bundle")["bundle_dir"]
    run = tmp_path / "run"
    run.mkdir()

    try:
        evaluate_bundle_outputs(toy_task, bundle / "current", run, overwrite=False, skip_judges=True)
    except FileExistsError as exc:
        assert "run directory already exists" in str(exc)
    else:
        raise AssertionError("expected FileExistsError")
