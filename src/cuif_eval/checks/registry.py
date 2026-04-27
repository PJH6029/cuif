from __future__ import annotations

from typing import Callable

from ..types import CheckResult, CheckSpec, Manifest, TurnSpec
from ..artifacts import RunWorkspace
from .core import file_exists
from .judge import judge_rubric
from .pptx import (
    pptx_bbox_region,
    pptx_chart_data,
    pptx_formula_present,
    pptx_image_count,
    pptx_image_match,
    pptx_preservation_diff,
    pptx_slide_count,
    pptx_style_check,
    pptx_text_contains,
    rendered_layout_review,
)

CheckFn = Callable[[CheckSpec, TurnSpec, Manifest, RunWorkspace, dict], CheckResult]

REGISTRY: dict[str, CheckFn] = {
    "file_exists": file_exists,
    "pptx_slide_count": pptx_slide_count,
    "pptx_text_contains": pptx_text_contains,
    "pptx_bbox_region": pptx_bbox_region,
    "pptx_style_check": pptx_style_check,
    "pptx_chart_data": pptx_chart_data,
    "pptx_image_count": pptx_image_count,
    "pptx_image_match": pptx_image_match,
    "pptx_formula_present": pptx_formula_present,
    "pptx_preservation_diff": pptx_preservation_diff,
    "rendered_layout_review": rendered_layout_review,
    "rendered_image_similarity": rendered_layout_review,
    "llm_text_rubric": judge_rubric,
    "vlm_layout_rubric": judge_rubric,
}


def get_check(evaluator: str) -> CheckFn:
    return REGISTRY[evaluator]
