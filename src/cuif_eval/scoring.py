from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .checks.registry import get_check
from .types import CheckResult, CheckSpec, Manifest, TurnSpec
from .artifacts import RunWorkspace


def blocked_result(spec: CheckSpec, turn: TurnSpec, blocked_by: list[str]) -> CheckResult:
    return CheckResult(
        check_id=spec.id,
        turn_id=turn.id,
        evaluator=spec.evaluator,
        artifact=spec.artifact,
        status="blocked",
        points=spec.points,
        earned_points=0.0,
        depends_on=spec.depends_on,
        evidence={"blocked_by": blocked_by},
        message=f"Blocked by failed/skipped dependencies: {', '.join(blocked_by)}",
        optional=spec.optional,
        diagnostic=spec.diagnostic,
        description=spec.description,
    )


def evaluate_manifest(manifest: Manifest, workspace: RunWorkspace, *, skip_judges: bool = False, judge_base_url: str | None = None, judge_model: str | None = None, judge_api_key_env: str = "OPENAI_API_KEY", refresh_judge_cache: bool = False) -> list[CheckResult]:
    context = {
        "skip_judges": skip_judges,
        "judge_base_url": judge_base_url,
        "judge_model": judge_model,
        "judge_api_key_env": judge_api_key_env,
        "refresh_judge_cache": refresh_judge_cache,
    }
    results: list[CheckResult] = []
    by_id: dict[str, CheckResult] = {}
    for turn in manifest.turns:
        for spec in turn.checks:
            blocked_by = [dep for dep in spec.depends_on if by_id.get(dep) is None or by_id[dep].status != "pass"]
            if blocked_by:
                result = blocked_result(spec, turn, blocked_by)
            else:
                try:
                    result = get_check(spec.evaluator)(spec, turn, manifest, workspace, context)
                except Exception as exc:  # keep evaluator-visible errors in report
                    result = CheckResult(
                        check_id=spec.id,
                        turn_id=turn.id,
                        evaluator=spec.evaluator,
                        artifact=spec.artifact,
                        status="error",
                        points=spec.points,
                        earned_points=0.0,
                        depends_on=spec.depends_on,
                        evidence={"error_type": type(exc).__name__, "error": str(exc)},
                        message=f"Evaluator error: {exc}",
                        optional=spec.optional,
                        diagnostic=spec.diagnostic,
                        description=spec.description,
                    )
            results.append(result)
            by_id[result.check_id] = result
    return results


def aggregate_results(results: list[CheckResult]) -> dict[str, Any]:
    by_turn: dict[str, dict[str, Any]] = defaultdict(lambda: {"earned_points": 0.0, "possible_points": 0.0, "checks": [], "status_counts": Counter()})
    status_counts: Counter[str] = Counter()
    preservation_failures: list[str] = []
    blocked_checks: list[str] = []
    lost_points = 0.0
    possible = 0.0
    earned = 0.0

    for result in results:
        status_counts[result.status] += 1
        turn_summary = by_turn[result.turn_id]
        turn_summary["checks"].append(result.check_id)
        turn_summary["status_counts"][result.status] += 1
        if not result.diagnostic:
            possible += result.points
            earned += result.earned_points
            turn_summary["possible_points"] += result.points
            turn_summary["earned_points"] += result.earned_points
            if result.status in {"fail", "blocked", "error"}:
                lost_points += max(0.0, result.points - result.earned_points)
        if result.status == "blocked":
            blocked_checks.append(result.check_id)
        if result.evaluator == "pptx_preservation_diff" and result.status != "pass":
            preservation_failures.append(result.check_id)

    per_turn = {}
    for turn_id, summary in by_turn.items():
        total = float(summary["possible_points"])
        per_turn[turn_id] = {
            "earned_points": float(summary["earned_points"]),
            "possible_points": total,
            "score": float(summary["earned_points"]) / total if total else 1.0,
            "checks": summary["checks"],
            "status_counts": dict(summary["status_counts"]),
        }

    return {
        "earned_points": earned,
        "possible_points": possible,
        "final_score": earned / possible if possible else 1.0,
        "lost_points": lost_points,
        "status_counts": dict(status_counts),
        "per_turn": per_turn,
        "blocked_checks": blocked_checks,
        "preservation_failures": preservation_failures,
        "regressions": preservation_failures,
    }
