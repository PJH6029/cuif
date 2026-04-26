from __future__ import annotations

import time

from ..artifacts import RunWorkspace
from ..types import Manifest
from .base import AdapterResult


class ManualAdapter:
    name = "manual"

    def run(self, manifest: Manifest, workspace: RunWorkspace, *, selected_turns: list[str] | None = None, invocation_mode: str = "whole_task", config: dict | None = None) -> AdapterResult:
        started = time.monotonic()
        selected = set(selected_turns or [turn.id for turn in manifest.turns])
        instruction_dir = workspace.work_dir / "manual_instructions"
        instruction_dir.mkdir(parents=True, exist_ok=True)
        logs: list[str] = []
        for turn in manifest.turns:
            if turn.id not in selected:
                continue
            path = instruction_dir / f"{turn.id}.md"
            path.write_text(f"# {manifest.title} / {turn.id}\n\n{turn.instruction}\n\nExpected output: `{turn.expected_output}` under `{workspace.outputs_dir / turn.id}`.\n", encoding="utf-8")
            logs.append(f"Wrote manual instructions: {path}")
        return AdapterResult(adapter=self.name, status="prepared", logs=logs, timings={"seconds": time.monotonic() - started})
