from __future__ import annotations

import shutil

import yaml
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

from cuif_eval.runner import run_task
from cuif_eval.pptx.extract import extract_charts, extract_shapes, extract_text_by_slide, slide_count


def _write_chart_deck(path):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    data = CategoryChartData()
    data.categories = ["Germany", "India", "United States", "China"]
    data.add_series("2015", [30.0, 14.9, 13.6, 23.9])
    data.add_series("2021", [39.8, 19.1, 20.3, 28.4])
    chart_shape = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1), Inches(8), Inches(4.5), data)
    chart_shape.name = "renewable_share_clustered_chart"
    prs.save(path)


def test_pptx_extraction_reads_slide_text_bbox_and_style(toy_task):
    pptx = toy_task / "mock_outputs" / "final" / "result.pptx"
    assert slide_count(pptx) == 2
    text = extract_text_by_slide(pptx)
    assert any("CUIF PoC Dashboard" in " ".join(values) for values in text.values())
    title = [s for s in extract_shapes(pptx) if "CUIF PoC Dashboard" in s.text][0]
    assert 0.05 <= title.x <= 0.15
    assert any(run.font_color == "#1F4E79" and run.bold for run in title.runs)


def test_pptx_chart_data_check_reads_native_chart_series(tmp_path):
    task = tmp_path / "chart_task"
    (task / "artifacts").mkdir(parents=True)
    (task / "mock_outputs" / "turn1").mkdir(parents=True)
    _write_chart_deck(task / "artifacts" / "seed.pptx")
    shutil.copy2(task / "artifacts" / "seed.pptx", task / "mock_outputs" / "turn1" / "result.pptx")
    (task / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "manifest_version": "0.1",
                "id": "chart_task",
                "title": "Chart data smoke task",
                "primary_artifact_family": "pptx",
                "artifact_families": ["pptx"],
                "tracks": ["open_tool"],
                "artifacts": {
                    "package": {"seed": {"path": "artifacts/seed.pptx", "type": "pptx", "role": "seed"}},
                    "expected_outputs": {"turn1": {"result": {"path": "result.pptx", "type": "pptx"}}},
                },
                "turns": [
                    {
                        "id": "turn1",
                        "instruction": "Create the chart.",
                        "expected_output": "result",
                        "checks": [
                            {"id": "exists", "evaluator": "file_exists", "artifact": "run.outputs.turn1.result", "points": 1},
                            {
                                "id": "chart_data",
                                "evaluator": "pptx_chart_data",
                                "artifact": "run.outputs.turn1.result",
                                "points": 4,
                                "params": {
                                    "selector": {"slide": 1, "name": "renewable_share_clustered_chart"},
                                    "chart_type": "COLUMN_CLUSTERED",
                                    "categories": ["Germany", "India", "United States", "China"],
                                    "series": [
                                        {"name": "2015", "values": [30.0, 14.9, 13.6, 23.9]},
                                        {"name": "2021", "values": [39.8, 19.1, 20.3, 28.4]},
                                    ],
                                    "value_tolerance": 0.01,
                                },
                            },
                        ],
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    charts = extract_charts(task / "mock_outputs" / "turn1" / "result.pptx")
    assert charts[0].categories == ["Germany", "India", "United States", "China"]

    result = run_task(task, adapter_name="mock", out=tmp_path / "run", skip_judges=True)
    statuses = {r.check_id: r.status for r in result["results"]}
    assert statuses["chart_data"] == "pass"


def test_passing_toy_task_has_required_pptx_checks_pass(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True)
    statuses = {r.check_id: r.status for r in result["results"]}
    assert statuses["title_present"] == "pass"
    assert statuses["title_region"] == "pass"
    assert statuses["brand_title_style"] == "pass"
    assert statuses["slide2_preserved"] == "pass"
    assert statuses["turn1_rendered_review"] in {"pass", "skipped", "blocked"}
    assert statuses["optional_llm_summary_judge"] == "skipped"


def test_broken_fixture_catches_text_style_layout_and_preservation_failures(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "broken", skip_judges=True, adapter_config={"mock_outputs_dir": "mock_outputs_broken"})
    statuses = {r.check_id: r.status for r in result["results"]}
    assert statuses["final_title_present"] == "fail"
    assert statuses["brand_title_style"] == "blocked"
    assert statuses["title_layout_preserved"] == "blocked"
    assert statuses["slide2_preserved"] == "fail"
