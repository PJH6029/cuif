from __future__ import annotations

from pathlib import Path
from typing import Any

from ..artifacts import resolve_artifact_ref
from ..pptx.diff import text_preservation_diff
from ..pptx.extract import contains_text, find_shapes, slide_count
from ..pptx.render import render_pptx_previews
from ..types import CheckResult, CheckSpec, Manifest, TurnSpec
from .core import make_result


def _missing(path: Path, spec: CheckSpec, turn: TurnSpec) -> CheckResult | None:
    if not path.exists():
        return make_result(spec, turn, "fail", evidence={"path": str(path), "exists": False}, message=f"PPTX artifact missing: {path}")
    return None


def pptx_slide_count(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    expected = int(spec.params.get("count"))
    actual = slide_count(path)
    ok = actual == expected
    return make_result(
        spec,
        turn,
        "pass" if ok else "fail",
        earned=spec.points,
        evidence={"path": str(path), "expected": expected, "actual": actual},
        message=f"Slide count {actual} matched expected {expected}" if ok else f"Slide count {actual} did not match expected {expected}",
    )


def pptx_text_contains(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    texts = spec.params.get("texts") or [spec.params.get("text")]
    texts = [str(text) for text in texts if text]
    missing = [text for text in texts if not contains_text(path, text, case_sensitive=bool(spec.params.get("case_sensitive", False)))]
    ok = not missing
    return make_result(
        spec,
        turn,
        "pass" if ok else "fail",
        earned=spec.points,
        evidence={"path": str(path), "required_texts": texts, "missing_texts": missing},
        message="All required PPTX text was present" if ok else f"Missing required PPTX text: {missing}",
    )


def pptx_bbox_region(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    selector = spec.params.get("selector", {})
    region = spec.params.get("region", {})
    tolerance = float(spec.params.get("tolerance", 0.0))
    shapes = find_shapes(path, selector)
    if not shapes:
        return make_result(spec, turn, "fail", evidence={"selector": selector}, message=f"No PPTX shape matched selector {selector}")
    shape = shapes[0]
    if "slide" in region and shape.slide != int(region["slide"]):
        ok = False
    else:
        ok = (
            shape.x >= float(region.get("x_min", 0)) - tolerance
            and shape.y >= float(region.get("y_min", 0)) - tolerance
            and shape.x_max <= float(region.get("x_max", 1)) + tolerance
            and shape.y_max <= float(region.get("y_max", 1)) + tolerance
        )
    evidence = {
        "selector": selector,
        "region": region,
        "tolerance": tolerance,
        "shape": {"slide": shape.slide, "x": shape.x, "y": shape.y, "x_max": shape.x_max, "y_max": shape.y_max, "text": shape.text},
    }
    return make_result(spec, turn, "pass" if ok else "fail", earned=spec.points, evidence=evidence, message="Shape bbox is inside requested region" if ok else "Shape bbox is outside requested region")


def _normalize_color(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    if not text.startswith("#"):
        text = f"#{text}"
    return text


def pptx_style_check(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    shapes = find_shapes(path, spec.params.get("selector", {}))
    if not shapes:
        return make_result(spec, turn, "fail", evidence={"selector": spec.params.get("selector", {})}, message="No shape matched selector for style check")
    shape = shapes[0]
    runs = [run for run in shape.runs if run.text.strip()] or shape.runs
    failures: list[str] = []
    actual: dict[str, Any] = {}
    if "font_size_pt" in spec.params:
        expected = float(spec.params["font_size_pt"])
        tolerance = float(spec.params.get("font_size_tolerance", 0.1))
        values = [run.font_size_pt for run in runs if run.font_size_pt is not None]
        actual["font_size_pt"] = values
        if not values or all(abs(value - expected) > tolerance for value in values):
            failures.append(f"font_size_pt expected {expected}±{tolerance}, got {values}")
    if "font_color" in spec.params:
        expected_color = _normalize_color(spec.params.get("font_color"))
        colors = [_normalize_color(run.font_color) for run in runs if run.font_color is not None]
        actual["font_color"] = colors
        if expected_color not in colors:
            failures.append(f"font_color expected {expected_color}, got {colors}")
    if "bold" in spec.params:
        expected_bold = bool(spec.params.get("bold"))
        bolds = [run.bold for run in runs]
        actual["bold"] = bolds
        if expected_bold not in bolds:
            failures.append(f"bold expected {expected_bold}, got {bolds}")
    ok = not failures
    return make_result(spec, turn, "pass" if ok else "fail", earned=spec.points, evidence={"selector": spec.params.get("selector", {}), "actual": actual, "failures": failures}, message="Style check passed" if ok else "; ".join(failures))


def pptx_preservation_diff(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    candidate = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(candidate, spec, turn):
        return miss
    reference_ref = spec.params.get("reference")
    if not reference_ref:
        return make_result(spec, turn, "error", evidence={}, message="preservation check requires params.reference")
    reference = resolve_artifact_ref(manifest, workspace, str(reference_ref))
    if not reference.exists():
        return make_result(spec, turn, "blocked", evidence={"reference": str(reference)}, message=f"Reference artifact missing: {reference}")
    diff = text_preservation_diff(candidate, reference, spec.params)
    ok = bool(diff["match"])
    return make_result(spec, turn, "pass" if ok else "fail", earned=spec.points, evidence={"candidate": str(candidate), "reference": str(reference), **diff}, message="Protected content/layout preserved" if ok else "Preservation differences detected")


def rendered_layout_review(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    preview = render_pptx_previews(path, workspace.previews_dir, f"scoring_{turn.id}_{spec.id}")
    if preview["status"] != "rendered":
        status = "skipped" if spec.optional else "blocked"
        return make_result(spec, turn, status, evidence=preview, message=preview.get("message", "Rendered preview unavailable"))
    return make_result(spec, turn, "pass", earned=spec.points, evidence=preview, message="Rendered preview generated for layout review")
