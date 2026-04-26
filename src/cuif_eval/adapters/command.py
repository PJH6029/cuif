from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path

from ..artifacts import RunWorkspace
from ..types import Manifest, TurnSpec
from .base import AdapterResult


def build_command_env(manifest: Manifest, workspace: RunWorkspace, turn: TurnSpec) -> dict[str, str]:
    return {
        "CUIF_TASK_DIR": str(workspace.task_copy_dir),
        "CUIF_WORK_DIR": str(workspace.work_dir),
        "CUIF_OUTPUT_DIR": str(workspace.outputs_dir / turn.id),
        "CUIF_TURN_ID": turn.id,
        "CUIF_INSTRUCTION_FILE": str(workspace.work_dir / "instructions" / f"{turn.id}.txt"),
    }


class CommandAdapter:
    name = "command"

    def run(self, manifest: Manifest, workspace: RunWorkspace, *, selected_turns: list[str] | None = None, invocation_mode: str = "per_turn", config: dict | None = None) -> AdapterResult:
        started = time.monotonic()
        config = config or {}
        command_template = config.get("command")
        selected = set(selected_turns or [turn.id for turn in manifest.turns])
        instruction_dir = workspace.work_dir / "instructions"
        instruction_dir.mkdir(parents=True, exist_ok=True)
        logs: list[str] = []
        errors: list[str] = []
        for turn in manifest.turns:
            if turn.id not in selected:
                continue
            env = build_command_env(manifest, workspace, turn)
            Path(env["CUIF_OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
            Path(env["CUIF_INSTRUCTION_FILE"]).write_text(turn.instruction, encoding="utf-8")
            logs.append("Prepared command env for " + turn.id + ": " + ", ".join(f"{k}={v}" for k, v in env.items()))
            if command_template:
                command = command_template.format(**env)
                completed = subprocess.run(shlex.split(command), env={**os.environ, **env}, cwd=workspace.work_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                logs.append(completed.stdout)
                if completed.returncode != 0:
                    errors.append(f"Command for {turn.id} exited {completed.returncode}: {completed.stderr}")
        status = "succeeded" if not errors and command_template else "prepared" if not errors else "failed"
        return AdapterResult(adapter=self.name, status=status, logs=logs, errors=errors, timings={"seconds": time.monotonic() - started})
