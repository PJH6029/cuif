from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageOps

from ..artifacts import resolve_artifact_ref
from ..pptx.diff import text_preservation_diff
from ..pptx.extract import contains_text, extract_text_by_slide, find_charts, find_images, find_shapes, slide_count
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


def _bbox_inside(item: Any, region: dict[str, Any], tolerance: float) -> bool:
    if "slide" in region and item.slide != int(region["slide"]):
        return False
    return (
        item.x >= float(region.get("x_min", 0)) - tolerance
        and item.y >= float(region.get("y_min", 0)) - tolerance
        and item.x_max <= float(region.get("x_max", 1)) + tolerance
        and item.y_max <= float(region.get("y_max", 1)) + tolerance
    )


def pptx_image_count(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    selector = spec.params.get("selector", {})
    images = find_images(path, selector)
    expected = spec.params.get("count")
    minimum = spec.params.get("min_count")
    if expected is not None:
        ok = len(images) == int(expected)
        message = f"Found {len(images)} images; expected exactly {expected}"
    else:
        min_count = int(minimum if minimum is not None else 1)
        ok = len(images) >= min_count
        message = f"Found {len(images)} images; expected at least {min_count}"
    evidence = {
        "selector": selector,
        "images": [
            {
                "slide": image.slide,
                "shape_name": image.shape_name,
                "content_type": image.content_type,
                "sha256": image.sha256,
                "bbox": {"x": image.x, "y": image.y, "x_max": image.x_max, "y_max": image.y_max},
            }
            for image in images
        ],
    }
    return make_result(spec, turn, "pass" if ok else "fail", earned=spec.points, evidence=evidence, message=message)


def _open_image(blob_or_path: bytes | Path) -> Image.Image:
    if isinstance(blob_or_path, bytes):
        image = Image.open(io.BytesIO(blob_or_path))
    else:
        image = Image.open(blob_or_path)
    return image.convert("RGB")


def _crop_to_content(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    mask = gray.point(lambda value: 255 if value < 248 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return image
    left, top, right, bottom = bbox
    pad = max(4, int(0.03 * max(image.size)))
    return image.crop((max(0, left - pad), max(0, top - pad), min(image.width, right + pad), min(image.height, bottom + pad)))


def _prepared_image(image: Image.Image, size: tuple[int, int] = (160, 120)) -> Image.Image:
    image = _crop_to_content(image)
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def _dhash(image: Image.Image, *, width: int = 17, height: int = 16) -> list[bool]:
    gray = ImageOps.grayscale(image.resize((width, height), Image.Resampling.LANCZOS))
    pixels = list(gray.tobytes())
    bits: list[bool] = []
    for y in range(height):
        row = pixels[y * width : (y + 1) * width]
        bits.extend(row[x] > row[x + 1] for x in range(width - 1))
    return bits


def _image_similarity(candidate_blob: bytes, reference_path: Path) -> float:
    candidate = _prepared_image(_open_image(candidate_blob))
    reference = _prepared_image(_open_image(reference_path))
    diff = ImageChops.difference(candidate, reference).convert("L")
    histogram = diff.histogram()
    pixels = candidate.width * candidate.height
    rms = math.sqrt(sum((value * value) * count for value, count in enumerate(histogram)) / max(1, pixels))
    rms_similarity = max(0.0, 1.0 - (rms / 255.0))
    cand_hash = _dhash(candidate)
    ref_hash = _dhash(reference)
    distance = sum(1 for left, right in zip(cand_hash, ref_hash, strict=True) if left != right)
    hash_similarity = 1.0 - (distance / len(cand_hash))
    return (0.6 * rms_similarity) + (0.4 * hash_similarity)


def pptx_image_match(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    source_ref = spec.params.get("source")
    if not source_ref:
        return make_result(spec, turn, "error", evidence={}, message="image match check requires params.source")
    reference = resolve_artifact_ref(manifest, workspace, str(source_ref))
    if not reference.exists():
        return make_result(spec, turn, "blocked", evidence={"reference": str(reference)}, message=f"Reference image missing: {reference}")
    selector = spec.params.get("selector", {})
    images = find_images(path, selector)
    if not images:
        return make_result(spec, turn, "fail", evidence={"selector": selector}, message=f"No PPTX image matched selector {selector}")
    scored = sorted(((image, _image_similarity(image.blob, reference)) for image in images), key=lambda item: item[1], reverse=True)
    best_image, best_similarity = scored[0]
    threshold = float(spec.params.get("min_similarity", 0.88))
    failures: list[str] = []
    if best_similarity < threshold:
        failures.append(f"best similarity {best_similarity:.3f} below threshold {threshold:.3f}")
    region = spec.params.get("region")
    tolerance = float(spec.params.get("tolerance", 0.0))
    if region and not _bbox_inside(best_image, region, tolerance):
        failures.append("best matching image is outside requested region")
    evidence = {
        "selector": selector,
        "source": str(reference),
        "min_similarity": threshold,
        "best_similarity": best_similarity,
        "best_image": {
            "slide": best_image.slide,
            "shape_name": best_image.shape_name,
            "content_type": best_image.content_type,
            "sha256": best_image.sha256,
            "bbox": {"x": best_image.x, "y": best_image.y, "x_max": best_image.x_max, "y_max": best_image.y_max},
        },
        "region": region,
        "tolerance": tolerance,
        "candidate_count": len(images),
        "failures": failures,
    }
    return make_result(spec, turn, "pass" if not failures else "fail", earned=spec.points, evidence=evidence, message="Image match check passed" if not failures else "; ".join(failures))


def _normalize_formula(value: str) -> str:
    replacements = {
        "−": "-",
        "–": "-",
        "—": "-",
        "×": "x",
        "·": "*",
        "√": "sqrt",
        "⁄": "/",
        "𝐾": "K",
        "𝑄": "Q",
        "𝑉": "V",
        "ᵀ": "^T",
    }
    text = value
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.lower()
    return "".join(char for char in text if not char.isspace())


def pptx_formula_present(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict[str, Any]) -> CheckResult:
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    if miss := _missing(path, spec, turn):
        return miss
    formulas = spec.params.get("formulas") or [spec.params.get("formula")]
    formulas = [str(formula) for formula in formulas if formula]
    text_by_slide = extract_text_by_slide(path)
    haystack = _normalize_formula("\n".join("\n".join(values) for values in text_by_slide.values()))
    missing = [formula for formula in formulas if _normalize_formula(formula) not in haystack]
    failures: list[str] = []
    if missing:
        failures.append(f"missing formulas: {missing}")
    selector = spec.params.get("selector")
    region = spec.params.get("region")
    shape_evidence = None
    if selector and region:
        shapes = find_shapes(path, selector)
        if not shapes:
            failures.append(f"no formula shape matched selector {selector}")
        else:
            tolerance = float(spec.params.get("tolerance", 0.0))
            shape = shapes[0]
            shape_evidence = {"slide": shape.slide, "x": shape.x, "y": shape.y, "x_max": shape.x_max, "y_max": shape.y_max, "text": shape.text}
            if not _bbox_inside(shape, region, tolerance):
                failures.append("formula shape is outside requested region")
    evidence = {"required_formulas": formulas, "missing": missing, "selector": selector, "region": region, "shape": shape_evidence}
    return make_result(spec, turn, "pass" if not failures else "fail", earned=spec.points, evidence=evidence, message="Formula text check passed" if not failures else "; ".join(failures))


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
