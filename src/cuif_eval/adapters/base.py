from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..artifacts import RunWorkspace
from ..types import Manifest


@dataclass
class AdapterResult:
    adapter: str
    status: str
    outputs: dict[str, dict[str, str]] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "adapter": self.adapter,
            "status": self.status,
            "outputs": self.outputs,
            "logs": self.logs,
            "errors": self.errors,
            "timings": self.timings,
        }


class Adapter(Protocol):
    name: str

    def run(self, manifest: Manifest, workspace: RunWorkspace, *, selected_turns: list[str] | None = None, invocation_mode: str = "per_turn", config: dict | None = None) -> AdapterResult:
        ...
