from __future__ import annotations

from pathlib import Path
from typing import Any

from ..artifacts import resolve_artifact_ref
from ..pptx.diff import text_preservation_diff
from ..pptx.extract import contains_text, find_charts, find_shapes, slide_count
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


def _values_match(actual: list[Any], expected: list[Any], tolerance: float) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if len(actual) != len(expected):
        return False, [f"value count expected {len(expected)}, got {len(actual)}"]
    for idx, (actual_value, expected_value) in enumerate(zip(actual, expected, strict=True)):
        if isinstance(expected_value, (int, float)):
            try:
                actual_float = float(actual_value)
            except (TypeError, ValueError):
                failures.append(f"value {idx} expected numeric {expected_value}, got {actual_value!r}")
                continue
            if abs(actual_float - float(expected_value)) > tolerance:
                failures.append(f"value {idx} expected {expected_value}±{tolerance}, got {actual_float}")
        elif actual_value != expected_value:
            failures.append(f"value {idx} expected {expected_value!r}, got {actual_value!r}")
    return not failures, failures


def pptx_chart_data(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    selector = spec.params.get("selector", {})
    charts = find_charts(path, selector)
    if not charts:
        return make_result(spec, turn, "fail", evidence={"selector": selector}, message=f"No PPTX chart matched selector {selector}")

    chart = charts[0]
    tolerance = float(spec.params.get("value_tolerance", spec.params.get("tolerance", 0.0)))
    failures: list[str] = []

    expected_type = spec.params.get("chart_type")
    if expected_type is not None and chart.chart_type != str(expected_type):
        failures.append(f"chart_type expected {expected_type}, got {chart.chart_type}")

    expected_categories = spec.params.get("categories")
    if expected_categories is not None and chart.categories != [str(category) for category in expected_categories]:
        failures.append(f"categories expected {expected_categories}, got {chart.categories}")

    actual_series = {series.name: series.values for series in chart.series}
    for expected_series in spec.params.get("series", []):
        name = str(expected_series.get("name", ""))
        if name not in actual_series:
            failures.append(f"series {name!r} missing")
            continue
        ok, value_failures = _values_match(actual_series[name], list(expected_series.get("values", [])), tolerance)
        if not ok:
            failures.extend(f"series {name}: {failure}" for failure in value_failures)

    evidence = {
        "selector": selector,
        "chart": {
            "slide": chart.slide,
            "shape_name": chart.shape_name,
            "chart_type": chart.chart_type,
            "categories": chart.categories,
            "series": [{"name": series.name, "values": series.values} for series in chart.series],
            "bbox": {"x": chart.x, "y": chart.y, "x_max": chart.x_max, "y_max": chart.y_max},
        },
        "failures": failures,
        "value_tolerance": tolerance,
    }
    return make_result(spec, turn, "pass" if not failures else "fail", earned=spec.points, evidence=evidence, message="Chart data check passed" if not failures else "; ".join(failures))


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
