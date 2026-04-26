from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Status = Literal["pass", "fail", "blocked", "skipped", "error"]


@dataclass(frozen=True)
class CheckSpec:
    id: str
    evaluator: str
    artifact: str
    points: float
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    optional: bool = False
    diagnostic: bool = False
    description: str | None = None


@dataclass(frozen=True)
class TurnSpec:
    id: str
    instruction: str
    expected_output: str
    checks: list[CheckSpec]


@dataclass(frozen=True)
class Manifest:
    path: Path
    task_dir: Path
    raw: dict[str, Any]
    manifest_version: str
    id: str
    title: str
    primary_artifact_family: str
    artifact_families: list[str]
    tracks: list[str]
    package_artifacts: dict[str, dict[str, Any]]
    expected_outputs: dict[str, dict[str, dict[str, Any]]]
    turns: list[TurnSpec]
    review: dict[str, Any] = field(default_factory=dict)
    scoring: dict[str, Any] = field(default_factory=dict)
    judge: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    check_id: str
    turn_id: str
    evaluator: str
    artifact: str
    status: Status
    points: float
    earned_points: float
    depends_on: list[str]
    evidence: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    optional: bool = False
    diagnostic: bool = False
    description: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "turn_id": self.turn_id,
            "evaluator": self.evaluator,
            "artifact": self.artifact,
            "status": self.status,
            "points": self.points,
            "earned_points": self.earned_points,
            "depends_on": self.depends_on,
            "evidence": self.evidence,
            "message": self.message,
            "optional": self.optional,
            "diagnostic": self.diagnostic,
            "description": self.description,
        }
