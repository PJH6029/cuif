from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from .bundles import evaluate_bundle_outputs, export_task_bundle, stage_bundle_turn
from .scoring import aggregate_results


DEFAULT_AGENT = "codex-exec"
DEFAULT_PROMPT_TEMPLATE = (
    "Work only in this directory. Follow instruction.md. "
    "Save the result as {output_path}. "
    "You can use [@Computer Use](plugin://computer-use@openai-bundled)."
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class AgentTurnContext:
    agent: str
    bundle_dir: Path
    current_dir: Path
    log_dir: Path
    task_id: str
    task_title: str
    turn_id: str
    output_path: str
    prompt: str
    agent_bin: str | None
    agent_args: Sequence[str]


def _bundle_root(bundle_dir: str | Path) -> Path:
    path = Path(bundle_dir).resolve()
    if (path / ".cuif_bundle" / "bundle_metadata.json").exists():
        return path
    if path.name == "current" and (path.parent / ".cuif_bundle" / "bundle_metadata.json").exists():
        return path.parent
    raise FileNotFoundError(f"bundle metadata not found under bundle root or current/ workspace: {path}")


def _metadata_path(bundle_root: Path) -> Path:
    return bundle_root / ".cuif_bundle" / "bundle_metadata.json"


def _read_metadata(bundle_root: Path) -> dict[str, Any]:
    return json.loads(_metadata_path(bundle_root).read_text(encoding="utf-8"))


def _write_text(path: Path, text: str | None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")
    return path.as_posix()


def _write_json(path: Path, data: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path.as_posix()


def _safe_agent_name(agent: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", agent).strip("_") or "agent"


def _turn_ids(metadata: dict[str, Any]) -> list[str]:
    return [str(turn["id"]) for turn in metadata.get("turns", [])]


def _output_path_for_turn(metadata: dict[str, Any], turn_id: str) -> str:
    matches = [output for output in metadata.get("outputs", []) if output.get("turn") == turn_id]
    if not matches:
        raise ValueError(f"bundle metadata has no output path for turn: {turn_id}")
    return str(matches[0]["path"])


def _format_prompt(template: str, metadata: dict[str, Any], turn_id: str, output_path: str) -> str:
    return template.format(
        task_id=metadata.get("task_id", ""),
        task_title=metadata.get("task_title", ""),
        turn_id=turn_id,
        output_path=output_path,
    )


def _run_codex_exec_turn(context: AgentTurnContext, command_runner: CommandRunner) -> dict[str, Any]:
    agent_bin = context.agent_bin or "codex"
    command = [
        agent_bin,
        "exec",
        "--cd",
        str(context.current_dir),
        "--json",
        "--yolo",
        "--skip-git-repo-check",
        *context.agent_args,
        context.prompt,
    ]
    started = time.monotonic()
    completed = command_runner(
        command,
        cwd=context.current_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    elapsed = time.monotonic() - started
    stdout_path = _write_text(context.log_dir / f"{context.turn_id}.stdout.jsonl", completed.stdout)
    stderr_path = _write_text(context.log_dir / f"{context.turn_id}.stderr.log", completed.stderr)
    return {
        "turn": context.turn_id,
        "output_path": context.output_path,
        "command": command[:-1] + ["<prompt>"],
        "prompt": context.prompt,
        "returncode": completed.returncode,
        "seconds": elapsed,
        "stdout": stdout_path,
        "stderr": stderr_path,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


AGENT_RUNNERS: dict[str, Callable[[AgentTurnContext, CommandRunner], dict[str, Any]]] = {
    "codex-exec": _run_codex_exec_turn,
}


def run_agent_on_bundle(
    bundle_dir: str | Path,
    *,
    agent: str = DEFAULT_AGENT,
    agent_bin: str | None = None,
    agent_args: Sequence[str] | None = None,
    prompt_template: str = DEFAULT_PROMPT_TEMPLATE,
    command_runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    """Run an agent across all staged turns of an already exported bundle."""
    if agent not in AGENT_RUNNERS:
        available = ", ".join(sorted(AGENT_RUNNERS))
        raise ValueError(f"unknown agent: {agent}; available agents: {available}")

    bundle_root = _bundle_root(bundle_dir)
    metadata = _read_metadata(bundle_root)
    current_dir = bundle_root / metadata.get("agent_workspace", "current")
    log_dir = bundle_root / ".cuif_bundle" / "agent_run_logs" / _safe_agent_name(agent)
    turn_results: list[dict[str, Any]] = []
    agent_args = list(agent_args or [])

    for turn_id in _turn_ids(metadata):
        stage_bundle_turn(bundle_root, turn_id)
        metadata = _read_metadata(bundle_root)
        output_path = _output_path_for_turn(metadata, turn_id)
        prompt = _format_prompt(prompt_template, metadata, turn_id, output_path)
        context = AgentTurnContext(
            agent=agent,
            bundle_dir=bundle_root,
            current_dir=current_dir,
            log_dir=log_dir,
            task_id=str(metadata.get("task_id", "")),
            task_title=str(metadata.get("task_title", "")),
            turn_id=turn_id,
            output_path=output_path,
            prompt=prompt,
            agent_bin=agent_bin,
            agent_args=agent_args,
        )
        turn_result = AGENT_RUNNERS[agent](context, command_runner)
        turn_results.append(turn_result)
        _write_json(
            log_dir / "agent_run_summary.json",
            {
                "agent": agent,
                "task_id": metadata.get("task_id"),
                "bundle_dir": bundle_root.as_posix(),
                "current_dir": current_dir.as_posix(),
                "turns": turn_results,
            },
        )
        if int(turn_result["returncode"]) != 0:
            raise RuntimeError(f"{agent} failed for {turn_id} with exit code {turn_result['returncode']}; see {turn_result['stderr']}")

    _write_json(
        log_dir / "agent_run_summary.json",
        {
            "agent": agent,
            "task_id": metadata.get("task_id"),
            "bundle_dir": bundle_root.as_posix(),
            "current_dir": current_dir.as_posix(),
            "turns": turn_results,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "agent": agent,
        "bundle_dir": bundle_root,
        "current_dir": current_dir,
        "log_dir": log_dir,
        "turns": turn_results,
        "metadata": metadata,
    }


def run_and_evaluate_bundle(
    task_dir: str | Path,
    bundle_dir: str | Path,
    run_dir: str | Path,
    *,
    agent: str = DEFAULT_AGENT,
    agent_bin: str | None = None,
    agent_args: Sequence[str] | None = None,
    prompt_template: str = DEFAULT_PROMPT_TEMPLATE,
    overwrite_bundle: bool = False,
    overwrite_run: bool = True,
    include_source_references: bool = False,
    skip_judges: bool = False,
    judge_base_url: str | None = None,
    judge_model: str | None = None,
    judge_api_key_env: str = "OPENAI_API_KEY",
    judge_image_url_base: str | None = None,
    refresh_judge_cache: bool = False,
    command_runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    """Export a bundle, run a selected agent across turns, and evaluate outputs."""
    export = export_task_bundle(
        task_dir,
        bundle_dir,
        overwrite=overwrite_bundle,
        include_source_references=include_source_references,
    )
    agent_result = run_agent_on_bundle(
        export["bundle_dir"],
        agent=agent,
        agent_bin=agent_bin,
        agent_args=agent_args,
        prompt_template=prompt_template,
        command_runner=command_runner,
    )
    evaluated = evaluate_bundle_outputs(
        task_dir,
        agent_result["current_dir"],
        run_dir,
        overwrite=overwrite_run,
        skip_judges=skip_judges,
        judge_base_url=judge_base_url,
        judge_model=judge_model,
        judge_api_key_env=judge_api_key_env,
        judge_image_url_base=judge_image_url_base,
        refresh_judge_cache=refresh_judge_cache,
    )
    summary = aggregate_results(evaluated["results"])
    _write_json(
        agent_result["log_dir"] / "run_and_evaluate_summary.json",
        {
            "agent": agent,
            "task_id": export["manifest"].id,
            "bundle_dir": export["bundle_dir"].as_posix(),
            "current_dir": export["current_dir"].as_posix(),
            "run_dir": evaluated["workspace"].run_dir.as_posix(),
            "summary": summary,
            "turns": agent_result["turns"],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "agent": agent,
        "bundle": export,
        "agent_result": agent_result,
        "evaluation": evaluated,
        "summary": summary,
        "log_dir": agent_result["log_dir"],
    }
