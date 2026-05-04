from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .checks.registry import get_check
from .types import CheckResult, CheckSpec, Manifest, TurnSpec
from .artifacts import RunWorkspace

DEFAULT_THESIS_HEAVY_THRESHOLD = 0.60

BOILERPLATE_EVALUATORS = {"file_exists", "pptx_slide_count"}
DIAGNOSTIC_LAYOUT_EVALUATORS = {"rendered_layout_review", "rendered_image_similarity"}
THESIS_HEAVY_BUCKETS = {"layout_template_style", "native_editability", "preservation_regression"}
EVALUATOR_BUCKETS = {
    "pptx_text_contains": "content_source",
    "pptx_formula_present": "content_source",
    "llm_text_rubric": "content_source",
    "pptx_bbox_region": "layout_template_style",
    "pptx_style_check": "layout_template_style",
    "pptx_image_match": "layout_template_style",
    "vlm_layout_rubric": "layout_template_style",
    "pptx_chart_data": "native_editability",
    "pptx_preservation_diff": "preservation_regression",
    "pptx_image_count": "other",
}


def _bucket_for_check(spec: CheckSpec) -> str:
    if spec.evaluator in BOILERPLATE_EVALUATORS:
        return "boilerplate"
    if spec.diagnostic or spec.evaluator in DIAGNOSTIC_LAYOUT_EVALUATORS:
        return "diagnostic"
    return EVALUATOR_BUCKETS.get(spec.evaluator, "other")


def point_distribution(manifest: Manifest, *, threshold: float = DEFAULT_THESIS_HEAVY_THRESHOLD) -> dict[str, Any]:
    """Summarize manifest point allocation for layout-constraint task review.

    The thesis-heavy share deliberately excludes boilerplate file/slide checks and
    diagnostic-only rendered preview checks from the denominator. This keeps
    layout/style/template/preservation/native-editability points from being
    diluted or inflated by task-plumbing checks.
    """

    by_bucket: defaultdict[str, float] = defaultdict(float)
    by_evaluator: defaultdict[str, float] = defaultdict(float)
    checks: list[dict[str, Any]] = []
    total_points = 0.0
    excluded_points = 0.0
    thesis_heavy_points = 0.0

    for turn in manifest.turns:
        for spec in turn.checks:
            points = float(spec.points)
            bucket = _bucket_for_check(spec)
            excluded = bucket in {"boilerplate", "diagnostic"}
            thesis_heavy = bucket in THESIS_HEAVY_BUCKETS
            total_points += points
            by_bucket[bucket] += points
            by_evaluator[spec.evaluator] += points
            if excluded:
                excluded_points += points
            elif thesis_heavy:
                thesis_heavy_points += points
            checks.append(
                {
                    "turn_id": turn.id,
                    "check_id": spec.id,
                    "evaluator": spec.evaluator,
                    "points": points,
                    "bucket": bucket,
                    "excluded_from_review_denominator": excluded,
                    "thesis_heavy": thesis_heavy and not excluded,
                    "diagnostic": spec.diagnostic,
                    "optional": spec.optional,
                }
            )

    review_points = total_points - excluded_points
    thesis_heavy_share = thesis_heavy_points / review_points if review_points else 1.0
    return {
        "threshold": float(threshold),
        "meets_threshold": thesis_heavy_share >= float(threshold),
        "total_points": total_points,
        "excluded_points": excluded_points,
        "review_points": review_points,
        "thesis_heavy_points": thesis_heavy_points,
        "thesis_heavy_share": thesis_heavy_share,
        "buckets": dict(sorted(by_bucket.items())),
        "evaluators": dict(sorted(by_evaluator.items())),
        "thesis_heavy_buckets": sorted(THESIS_HEAVY_BUCKETS),
        "excluded_buckets": ["boilerplate", "diagnostic"],
        "checks": checks,
    }


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


def evaluate_manifest(
    manifest: Manifest,
    workspace: RunWorkspace,
    *,
    skip_judges: bool = False,
    judge_base_url: str | None = None,
    judge_model: str | None = None,
    judge_api_key_env: str = "OPENAI_API_KEY",
    judge_image_url_base: str | None = None,
    refresh_judge_cache: bool = False,
) -> list[CheckResult]:
    context = {
        "skip_judges": skip_judges,
        "judge_base_url": judge_base_url,
        "judge_model": judge_model,
        "judge_api_key_env": judge_api_key_env,
        "judge_image_url_base": judge_image_url_base,
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
