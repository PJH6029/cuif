from __future__ import annotations

from cuif_eval.runner import run_task
from cuif_eval.pptx.extract import extract_shapes, extract_text_by_slide, slide_count


def test_pptx_extraction_reads_slide_text_bbox_and_style(toy_task):
    pptx = toy_task / "mock_outputs" / "final" / "result.pptx"
    assert slide_count(pptx) == 2
    text = extract_text_by_slide(pptx)
    assert any("CUIF PoC Dashboard" in " ".join(values) for values in text.values())
    title = [s for s in extract_shapes(pptx) if "CUIF PoC Dashboard" in s.text][0]
    assert 0.05 <= title.x <= 0.15
    assert any(run.font_color == "#1F4E79" and run.bold for run in title.runs)


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
