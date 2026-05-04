from __future__ import annotations

from cuif_eval.schema import load_manifest
from cuif_eval.scoring import aggregate_results
from cuif_eval.scoring import point_distribution
from cuif_eval.types import CheckResult


def result(check_id, turn_id, status, points=1, earned=0, evaluator="file_exists", deps=None, diagnostic=False):
    return CheckResult(check_id, turn_id, evaluator, "run.outputs.turn.result", status, points, earned, deps or [], diagnostic=diagnostic)


def test_aggregation_sums_per_turn_and_final_scores():
    summary = aggregate_results([
        result("a", "turn1", "pass", 2, 2),
        result("b", "turn1", "fail", 3, 0),
        result("c", "final", "blocked", 5, 0),
        result("d", "final", "skipped", 99, 0, diagnostic=True),
    ])
    assert summary["earned_points"] == 2
    assert summary["possible_points"] == 10
    assert summary["per_turn"]["turn1"]["possible_points"] == 5
    assert summary["blocked_checks"] == ["c"]
    assert summary["status_counts"]["skipped"] == 1


def test_preservation_failures_are_visible_as_regressions():
    summary = aggregate_results([result("preserve", "final", "fail", 3, 0, evaluator="pptx_preservation_diff")])
    assert summary["preservation_failures"] == ["preserve"]
    assert summary["regressions"] == ["preserve"]


def test_point_distribution_excludes_boilerplate_and_diagnostic_preview(mutate_manifest):
    def add_diagnostic_points(data):
        for turn in data["turns"]:
            for check in turn["checks"]:
                if check["id"] == "turn1_rendered_review":
                    check["points"] = 5

    manifest = load_manifest(mutate_manifest(add_diagnostic_points), skip_judges=True)
    distribution = point_distribution(manifest)

    assert distribution["buckets"]["boilerplate"] == 4
    assert distribution["buckets"]["diagnostic"] == 5
    assert distribution["review_points"] == 15
    assert distribution["thesis_heavy_points"] == 10
    assert distribution["thesis_heavy_share"] == 10 / 15
    assert distribution["meets_threshold"] is True
    rendered = next(check for check in distribution["checks"] if check["check_id"] == "turn1_rendered_review")
    assert rendered["excluded_from_review_denominator"] is True
