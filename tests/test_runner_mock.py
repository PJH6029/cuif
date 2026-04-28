from __future__ import annotations

import json

from cuif_eval.cli import build_parser
from cuif_eval.adapters.command import build_command_env
from cuif_eval.adapters.manual import ManualAdapter
from cuif_eval.artifacts import create_run_workspace
from cuif_eval.runner import run_task
from cuif_eval.schema import load_manifest


def test_mock_adapter_copies_outputs_and_records_metadata(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True, invocation_mode="per_turn")
    run = result["workspace"].run_dir
    assert (run / "outputs" / "turn1" / "result.pptx").exists()
    assert (run / "outputs" / "final" / "result.pptx").exists()
    metadata = json.loads((run / "run_metadata.json").read_text())
    assert metadata["adapter_status"] == "succeeded"
    assert metadata["invocation_mode"] == "per_turn"


def test_runner_supports_whole_task_mode(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True, invocation_mode="whole_task")
    assert result["adapter_result"].status == "succeeded"


def test_missing_mock_output_is_reported_as_run_failure(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True, adapter_config={"mock_outputs_dir": "does_not_exist"})
    assert result["adapter_result"].status == "failed"
    assert any(r.status in {"fail", "blocked"} for r in result["results"])


def test_manual_adapter_prepares_instructions_without_outputs(toy_task, tmp_path):
    manifest = load_manifest(toy_task / "manifest.yaml")
    workspace = create_run_workspace(toy_task, tmp_path / "manual")
    result = ManualAdapter().run(manifest, workspace)
    assert result.status == "prepared"
    assert (workspace.work_dir / "manual_instructions" / "turn1.md").exists()
    assert not (workspace.outputs_dir / "turn1" / "result.pptx").exists()


def test_command_adapter_environment_contract(toy_task, tmp_path):
    manifest = load_manifest(toy_task / "manifest.yaml")
    workspace = create_run_workspace(toy_task, tmp_path / "cmd")
    env = build_command_env(manifest, workspace, manifest.turns[0])
    assert set(env) == {"CUIF_TASK_DIR", "CUIF_WORK_DIR", "CUIF_OUTPUT_DIR", "CUIF_TURN_ID", "CUIF_INSTRUCTION_FILE"}
    assert env["CUIF_TASK_DIR"] == str(workspace.task_copy_dir)
    assert env["CUIF_TURN_ID"] == "turn1"


def test_command_template_flag_does_not_shadow_cli_subcommand():
    args = build_parser().parse_args(["run", "--task", "poc/tasks/toy_pptx_layout", "--adapter", "command", "--command", "echo {CUIF_TURN_ID}"])
    assert args.command == "run"
    assert args.command_template == "echo {CUIF_TURN_ID}"


def test_run_agent_parser_contract():
    args = build_parser().parse_args(
        [
            "run-agent",
            "--bundle",
            "output/bundles/toy",
            "--agent",
            "codex-exec",
            "--agent-arg=--model",
            "--agent-arg=gpt-5.5",
        ]
    )
    assert args.command == "run-agent"
    assert args.agent == "codex-exec"
    assert args.agent_arg == ["--model", "gpt-5.5"]


def test_run_and_evaluate_parser_contract():
    args = build_parser().parse_args(
        [
            "run-and-evaluate",
            "--task",
            "poc/tasks/toy_pptx_layout",
            "--bundle",
            "output/bundles/toy",
            "--run",
            "output/runs/toy_codex",
            "--agent",
            "codex-exec",
        ]
    )
    assert args.command == "run-and-evaluate"
    assert args.agent == "codex-exec"
