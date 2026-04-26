from __future__ import annotations

from pathlib import Path
from typing import Any

from ..types import CheckResult, CheckSpec, Manifest, TurnSpec
from ..artifacts import RunWorkspace, resolve_artifact_ref


def make_result(spec: CheckSpec, turn: TurnSpec, status: str, *, earned: float = 0.0, evidence: dict[str, Any] | None = None, message: str = "") -> CheckResult:
    return CheckResult(
        check_id=spec.id,
        turn_id=turn.id,
        evaluator=spec.evaluator,
        artifact=spec.artifact,
        status=status,  # type: ignore[arg-type]
        points=spec.points,
        earned_points=earned if status == "pass" else 0.0,
        depends_on=spec.depends_on,
        evidence=evidence or {},
        message=message,
        optional=spec.optional,
        diagnostic=spec.diagnostic,
        description=spec.description,
    )


def file_exists(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace: RunWorkspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    exists = Path(path).exists()
    return make_result(
        spec,
        turn,
        "pass" if exists else "fail",
        earned=spec.points,
        evidence={"path": str(path), "exists": exists},
        message=f"File exists: {path}" if exists else f"Missing expected file: {path}",
    )
