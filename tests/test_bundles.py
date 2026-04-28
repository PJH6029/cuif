from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from cuif_eval.agent_runners import run_agent_on_bundle, run_and_evaluate_bundle
from cuif_eval.bundles import evaluate_bundle_outputs, export_task_bundle, stage_bundle_turn
from cuif_eval.scoring import aggregate_results


def test_export_bundle_stages_agent_workspace_without_gold_or_manifest(toy_task, tmp_path):
    result = export_task_bundle(toy_task, tmp_path / "bundle")
    bundle = result["bundle_dir"]
    current = result["current_dir"]

    assert (current / "AGENTS.md").exists()
    assert (current / "instruction.md").read_text(encoding="utf-8").startswith("# Toy PPTX layout smoke task / turn1")
    assert (current / "seed.pptx").exists()
    assert (current / "inputs" / "turn1" / "sketch.svg").exists()
    assert (current / "outputs" / "turn1").is_dir()
    assert (current / "outputs" / "final").is_dir()
    assert not (current / "manifest.yaml").exists()
    assert not (current / "gold").exists()
    assert not list(current.rglob("*gold*"))

    metadata = json.loads((bundle / ".cuif_bundle" / "bundle_metadata.json").read_text(encoding="utf-8"))
    assert metadata["task_id"] == "toy_pptx_layout"
    assert metadata["active_turn"] == "turn1"
    assert metadata["staged_turns"] == ["turn1"]
    assert metadata["turn_inputs"]["turn1"][0]["workspace_path"] == "inputs/turn1/sketch.svg"
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


def test_stage_bundle_turn_reveals_only_that_turns_new_inputs(tmp_path):
    task = tmp_path / "turn_input_task"
    repo_root = Path(__file__).resolve().parents[1]
    shutil.copytree(repo_root / "poc" / "tasks" / "aurora_paper_review_deck", task)
    result = export_task_bundle(task, tmp_path / "bundle")
    bundle = result["bundle_dir"]
    current = result["current_dir"]

    assert (current / "inputs" / "turn1" / "paper_brief.txt").exists()
    assert (current / "inputs" / "turn1" / "layout_sketch.svg").exists()
    assert not (current / "inputs" / "turn2" / "source_figure.svg").exists()
    assert not (current / "inputs" / "final" / "style_reference.svg").exists()

    staged = stage_bundle_turn(bundle, "turn2")
    assert staged["turn"] == "turn2"
    assert (current / "inputs" / "turn2" / "source_figure.svg").exists()
    assert not (current / "inputs" / "final" / "style_reference.svg").exists()
    assert "source_figure.svg" in (current / "instruction.md").read_text(encoding="utf-8")

    metadata = json.loads((bundle / ".cuif_bundle" / "bundle_metadata.json").read_text(encoding="utf-8"))
    assert metadata["active_turn"] == "turn2"
    assert metadata["staged_turns"] == ["turn1", "turn2"]


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


def test_run_agent_runs_turns_without_evaluating_outputs(toy_task, tmp_path):
    calls = []

    def fake_codex_run(command, *, cwd, text, stdout, stderr, check):
        calls.append(command)
        prompt = command[-1]
        match = re.search(r"outputs/([^/]+)/result\.pptx", prompt)
        assert match, prompt
        turn_id = match.group(1)
        destination = cwd / "outputs" / turn_id / "result.pptx"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(toy_task / "mock_outputs" / turn_id / "result.pptx", destination)
        return subprocess.CompletedProcess(command, 0, stdout='{"event":"done"}\n', stderr="")

    bundle = export_task_bundle(toy_task, tmp_path / "bundle")["bundle_dir"]
    result = run_agent_on_bundle(
        bundle,
        agent="codex-exec",
        command_runner=fake_codex_run,
    )

    assert [turn["turn"] for turn in result["turns"]] == ["turn1", "final"]
    assert len(calls) == 2
    assert calls[0][:7] == ["codex", "exec", "--cd", str(tmp_path / "bundle" / "current"), "--json", "--yolo", "--skip-git-repo-check"]
    assert "outputs/turn1/result.pptx" in calls[0][-1]
    assert "outputs/final/result.pptx" in calls[1][-1]
    assert (tmp_path / "bundle" / ".cuif_bundle" / "agent_run_logs" / "codex-exec" / "turn1.stdout.jsonl").exists()
    assert not (tmp_path / "run" / "report.md").exists()


def test_run_and_evaluate_exports_runs_agent_and_evaluates(toy_task, tmp_path):
    def fake_codex_run(command, *, cwd, text, stdout, stderr, check):
        prompt = command[-1]
        match = re.search(r"outputs/([^/]+)/result\.pptx", prompt)
        assert match, prompt
        turn_id = match.group(1)
        destination = cwd / "outputs" / turn_id / "result.pptx"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(toy_task / "mock_outputs" / turn_id / "result.pptx", destination)
        return subprocess.CompletedProcess(command, 0, stdout='{"event":"done"}\n', stderr="")

    result = run_and_evaluate_bundle(
        toy_task,
        tmp_path / "bundle",
        tmp_path / "run",
        overwrite_bundle=True,
        skip_judges=True,
        command_runner=fake_codex_run,
    )

    assert [turn["turn"] for turn in result["agent_result"]["turns"]] == ["turn1", "final"]
    assert (tmp_path / "run" / "report.md").exists()
    assert result["summary"]["final_score"] == 1.0
