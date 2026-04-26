from __future__ import annotations

import json

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
    seed_assets = [asset for asset in report["review_assets"] if asset["artifact"] == "package.seed"]
    assert seed_assets
    assert seed_assets[0]["path"].startswith("task/")
    html = (run / "review" / "index.html").read_text()
    assert "Seed / Output / Gold Comparison" in html
    assert "optional_llm_summary_judge" in html


def test_broken_run_report_records_lost_points(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "broken", skip_judges=True, adapter_config={"mock_outputs_dir": "mock_outputs_broken"})
    report = json.loads((result["workspace"].run_dir / "report.json").read_text())
    assert report["summary"]["final_score"] < 1.0
    assert "slide2_preserved" in report["summary"]["preservation_failures"]
