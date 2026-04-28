from __future__ import annotations

import copy
import json
import shutil
from types import SimpleNamespace

import yaml

from cuif_eval.reports import write_review_html
from cuif_eval.runner import run_task


def test_reports_and_static_review_are_generated(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True)
    run = result["workspace"].run_dir
    report = json.loads((run / "report.json").read_text())
    report_text = (run / "report.json").read_text()
    assert (run / "report.md").exists()
    assert (run / "review" / "index.html").exists()
    assert report["summary"]["final_score"] == 1.0
    assert report["task"]["manifest"] == "task/manifest.yaml"
    assert report["artifacts"]["package.seed"].startswith("task/")
    assert str(toy_task) not in report_text
    assert str(run) not in report_text
    assert "per_turn" in report["summary"]
    assert "review_trajectory" in report
    assert [column["id"] for column in report["review_trajectory"]["columns"]] == ["seed", "turn1", "final"]
    assert report["review_trajectory"]["columns"][1]["instruction"].startswith("Create a two-slide dashboard")
    seed_assets = [asset for asset in report["review_assets"] if asset["artifact"] == "package.seed"]
    assert seed_assets
    assert seed_assets[0]["path"].startswith("task/")
    html = (run / "review" / "index.html").read_text()
    assert "Trajectory Comparison" in html
    assert "data-trajectory-instruction='turn1'" in html
    assert "Create a two-slide dashboard from the seed deck." in html
    assert "data-trajectory-comparison" in html
    assert "data-trajectory-cell" in html
    assert "data-trajectory-prev" in html
    assert "ArrowLeft" in html and "ArrowRight" in html
    assert "optional_llm_summary_judge" in html


def _write_manifest(task, data):
    (task / "manifest.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _make_two_turn_task(task):
    shutil.copy2(task / "artifacts" / "gold" / "turn1.pptx", task / "artifacts" / "gold" / "turn2.pptx")
    shutil.copytree(task / "mock_outputs" / "turn1", task / "mock_outputs" / "turn2")
    data = yaml.safe_load((task / "manifest.yaml").read_text(encoding="utf-8"))

    package = data["artifacts"]["package"]
    reordered_package = {}
    for key, value in package.items():
        reordered_package[key] = value
        if key == "gold_turn1":
            reordered_package["gold_turn2"] = {"path": "artifacts/gold/turn2.pptx", "type": "pptx", "role": "gold"}
    data["artifacts"]["package"] = reordered_package

    expected = data["artifacts"]["expected_outputs"]
    reordered_expected = {}
    for key, value in expected.items():
        reordered_expected[key] = value
        if key == "turn1":
            reordered_expected["turn2"] = {"result": {"path": "result.pptx", "type": "pptx"}}
    data["artifacts"]["expected_outputs"] = reordered_expected

    turn2 = copy.deepcopy(data["turns"][0])
    turn2["id"] = "turn2"
    turn2["instruction"] = "Continue the draft deck while preserving the protected context."
    turn2["checks"] = [
        {"id": "turn2_file_exists", "evaluator": "file_exists", "artifact": "run.outputs.turn2.result", "points": 1},
        {
            "id": "turn2_slide_count",
            "evaluator": "pptx_slide_count",
            "artifact": "run.outputs.turn2.result",
            "points": 1,
            "depends_on": ["turn2_file_exists"],
            "params": {"count": 2},
        },
    ]
    data["turns"].insert(1, turn2)
    _write_manifest(task, data)
    return task


def test_review_trajectory_includes_all_turns_and_one_final(copied_task, tmp_path):
    task = _make_two_turn_task(copied_task)
    result = run_task(task, adapter_name="mock", out=tmp_path / "run", skip_judges=True)
    run = result["workspace"].run_dir
    report = json.loads((run / "report.json").read_text())
    html = (run / "review" / "index.html").read_text()

    assert [column["id"] for column in report["review_trajectory"]["columns"]] == ["seed", "turn1", "turn2", "final"]
    assert report["review_trajectory"]["columns"][2]["instruction"] == "Continue the draft deck while preserving the protected context."
    assert html.count("data-trajectory-column='final'") == 1
    grid_start = html.index("data-trajectory-grid")
    header_start = html.index("data-trajectory-column='turn1'", grid_start)
    instruction_start = html.index("data-trajectory-instruction='turn1'", grid_start)
    seed_gold_start = html.index('<div class="trajectory-row-label">Seed / gold</div>', grid_start)
    assert header_start < instruction_start < seed_gold_start
    for label in ["Seed deck", "Turn 1 gold", "Turn 2 gold", "Final gold", "No seed output", "Turn 1 output", "Turn 2 output", "Final output"]:
        assert label in html
    for cell_id in ["seed-top", "turn1-top", "turn2-top", "final-top", "seed-bottom", "turn1-bottom", "turn2-bottom", "final-bottom"]:
        assert f"data-cell-id='{cell_id}'" in html


def test_review_trajectory_keeps_missing_output_cells(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "missing", skip_judges=True, adapter_config={"mock_outputs_dir": "does_not_exist"})
    run = result["workspace"].run_dir
    html = (run / "review" / "index.html").read_text()
    assert result["adapter_result"].status == "failed"
    assert "data-cell-id='turn1-bottom'" in html
    assert "data-cell-id='final-bottom'" in html
    assert "Agent output for Turn 1 was not produced." in html
    assert "Final agent output was not produced." in html
    turn1_start = html.index("data-cell-id='turn1-bottom'")
    final_start = html.index("data-cell-id='final-bottom'")
    turn1_block = html[turn1_start:final_start]
    assert "<img" not in turn1_block
    assert "trajectory-cell--not_produced" in turn1_block


def test_review_html_navigation_serializes_all_preview_images(tmp_path):
    review_dir = tmp_path / "review"
    review_dir.mkdir()
    report_data = {
        "task": {"title": "Injected nav report"},
        "summary": {"earned_points": 1.0, "possible_points": 1.0, "final_score": 1.0, "status_counts": {"pass": 1}},
        "checks": [],
        "review_assets": [],
        "review_trajectory": {
            "version": 1,
            "columns": [
                {
                    "id": "seed",
                    "label": "Seed",
                    "top": {
                        "label": "Seed deck",
                        "artifact": "package.seed",
                        "status": "rendered",
                        "path": "task/artifacts/seed.pptx",
                        "preview": {"images": ["previews/seed/slide1.png", "previews/seed/slide2.png"]},
                        "selectable": True,
                    },
                    "bottom": {"label": "No seed output", "status": "placeholder", "message": "Agent output starts after turn 1.", "preview": {"images": []}, "selectable": False},
                }
            ],
        },
    }

    write_review_html(report_data, SimpleNamespace(review_dir=review_dir))
    html = (review_dir / "index.html").read_text()
    assert "../previews/seed/slide1.png" in html
    assert "../previews/seed/slide2.png" in html
    assert "data-images=" in html
    assert "data-trajectory-prev" in html and "data-trajectory-next" in html
    assert "ArrowLeft" in html and "ArrowRight" in html


def test_broken_run_report_records_lost_points(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "broken", skip_judges=True, adapter_config={"mock_outputs_dir": "mock_outputs_broken"})
    report = json.loads((result["workspace"].run_dir / "report.json").read_text())
    assert report["summary"]["final_score"] < 1.0
    assert "slide2_preserved" in report["summary"]["preservation_failures"]
