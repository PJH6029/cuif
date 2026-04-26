from __future__ import annotations

import shutil
import time

from ..artifacts import RunWorkspace, resolve_run_output, safe_join
from ..types import Manifest
from .base import AdapterResult


class MockAdapter:
    name = "mock"

    def run(self, manifest: Manifest, workspace: RunWorkspace, *, selected_turns: list[str] | None = None, invocation_mode: str = "per_turn", config: dict | None = None) -> AdapterResult:
        started = time.monotonic()
        config = config or {}
        fixture_dir = safe_join(manifest.task_dir, config.get("mock_outputs_dir", "mock_outputs"))
        selected = set(selected_turns or [turn.id for turn in manifest.turns])
        outputs: dict[str, dict[str, str]] = {}
        logs = [f"Mock adapter invocation_mode={invocation_mode}", f"Fixture directory: {fixture_dir}"]
        errors: list[str] = []
        for turn in manifest.turns:
            if turn.id not in selected:
                continue
            outputs[turn.id] = {}
            for output_name, output_spec in manifest.expected_outputs.get(turn.id, {}).items():
                src = safe_join(fixture_dir / turn.id, output_spec["path"])
                dst = resolve_run_output(manifest, workspace, turn.id, output_name)
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not src.exists():
                    errors.append(f"Missing mock output for {turn.id}.{output_name}: {src}")
                    continue
                shutil.copy2(src, dst)
                outputs[turn.id][output_name] = str(dst)
                logs.append(f"Copied {src} -> {dst}")
        status = "succeeded" if not errors else "failed"
        result = AdapterResult(adapter=self.name, status=status, outputs=outputs, logs=logs, errors=errors, timings={"seconds": time.monotonic() - started})
        (workspace.logs_dir / "adapter_mock.log").write_text("\n".join(logs + errors), encoding="utf-8")
        return result
