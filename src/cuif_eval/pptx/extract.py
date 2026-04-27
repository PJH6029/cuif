from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pptx import Presentation


@dataclass(frozen=True)
class TextRunInfo:
    text: str
    font_size_pt: float | None
    font_color: str | None
    bold: bool | None


@dataclass(frozen=True)
class ShapeInfo:
    slide: int
    shape_name: str
    text: str
    x: float
    y: float
    w: float
    h: float
    runs: list[TextRunInfo]

    @property
    def x_max(self) -> float:
        return self.x + self.w

    @property
    def y_max(self) -> float:
        return self.y + self.h


@dataclass(frozen=True)
class ChartSeriesInfo:
    name: str
    values: list[float | str | None]


@dataclass(frozen=True)
class ChartInfo:
    slide: int
    shape_name: str
    chart_type: str
    x: float
    y: float
    w: float
    h: float
    categories: list[str]
    series: list[ChartSeriesInfo]

    @property
    def x_max(self) -> float:
        return self.x + self.w

    @property
    def y_max(self) -> float:
        return self.y + self.h


def slide_count(path: str | Path) -> int:
    return len(Presentation(str(path)).slides)


def _rgb_to_hex(value: Any) -> str | None:
    if value is None:
        return None
    try:
        rgb = value.rgb
    except Exception:
        return None
    if rgb is None:
        return None
    return f"#{str(rgb).upper()}"


def _shape_runs(shape: Any) -> list[TextRunInfo]:
    runs: list[TextRunInfo] = []
    if not getattr(shape, "has_text_frame", False):
        return runs
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            font = run.font
            runs.append(
                TextRunInfo(
                    text=run.text,
                    font_size_pt=float(font.size.pt) if font.size is not None else None,
                    font_color=_rgb_to_hex(font.color),
                    bold=font.bold,
                )
            )
    return runs


def extract_shapes(path: str | Path) -> list[ShapeInfo]:
    prs = Presentation(str(path))
    width = float(prs.slide_width)
    height = float(prs.slide_height)
    shapes: list[ShapeInfo] = []
    for sidx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            text = ""
            if getattr(shape, "has_text_frame", False):
                text = shape.text or ""
            try:
                left, top, sw, sh = float(shape.left), float(shape.top), float(shape.width), float(shape.height)
            except Exception:
                left = top = sw = sh = 0.0
            shapes.append(
                ShapeInfo(
                    slide=sidx,
                    shape_name=getattr(shape, "name", ""),
                    text=text,
                    x=left / width if width else 0.0,
                    y=top / height if height else 0.0,
                    w=sw / width if width else 0.0,
                    h=sh / height if height else 0.0,
                    runs=_shape_runs(shape),
                )
            )
    return shapes


def _chart_categories(chart: Any) -> list[str]:
    for plot in chart.plots:
        try:
            categories = plot.categories
        except Exception:
            continue
        return [str(getattr(category, "label", category)) for category in categories]
    return []


def _chart_values(series: Any) -> list[float | str | None]:
    values: list[float | str | None] = []
    for value in series.values:
        if value is None:
            values.append(None)
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            values.append(str(value))
    return values


def extract_charts(path: str | Path) -> list[ChartInfo]:
    prs = Presentation(str(path))
    width = float(prs.slide_width)
    height = float(prs.slide_height)
    charts: list[ChartInfo] = []
    for sidx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if not getattr(shape, "has_chart", False):
                continue
            chart = shape.chart
            try:
                left, top, sw, sh = float(shape.left), float(shape.top), float(shape.width), float(shape.height)
            except Exception:
                left = top = sw = sh = 0.0
            chart_type = getattr(getattr(chart, "chart_type", None), "name", None) or str(getattr(chart, "chart_type", ""))
            charts.append(
                ChartInfo(
                    slide=sidx,
                    shape_name=getattr(shape, "name", ""),
                    chart_type=str(chart_type),
                    x=left / width if width else 0.0,
                    y=top / height if height else 0.0,
                    w=sw / width if width else 0.0,
                    h=sh / height if height else 0.0,
                    categories=_chart_categories(chart),
                    series=[ChartSeriesInfo(name=str(series.name), values=_chart_values(series)) for series in chart.series],
                )
            )
    return charts


def extract_text_by_slide(path: str | Path) -> dict[int, list[str]]:
    text: dict[int, list[str]] = {}
    for shape in extract_shapes(path):
        if shape.text.strip():
            text.setdefault(shape.slide, []).append(" ".join(shape.text.split()))
    return text


def contains_text(path: str | Path, needle: str, *, case_sensitive: bool = False) -> bool:
    haystack = "\n".join("\n".join(v) for v in extract_text_by_slide(path).values())
    if case_sensitive:
        return needle in haystack
    return needle.lower() in haystack.lower()


def find_shapes(path: str | Path, selector: dict[str, Any] | None = None) -> list[ShapeInfo]:
    selector = selector or {}
    shapes = extract_shapes(path)
    slide = selector.get("slide")
    text_contains = selector.get("text_contains")
    name = selector.get("name")
    result: list[ShapeInfo] = []
    for shape in shapes:
        if slide is not None and shape.slide != int(slide):
            continue
        if text_contains is not None and str(text_contains).lower() not in shape.text.lower():
            continue
        if name is not None and str(name) != shape.shape_name:
            continue
        result.append(shape)
    return result


def find_charts(path: str | Path, selector: dict[str, Any] | None = None) -> list[ChartInfo]:
    selector = selector or {}
    charts = extract_charts(path)
    slide = selector.get("slide")
    name = selector.get("name")
    chart_type = selector.get("chart_type")
    result: list[ChartInfo] = []
    for chart in charts:
        if slide is not None and chart.slide != int(slide):
            continue
        if name is not None and str(name) != chart.shape_name:
            continue
        if chart_type is not None and str(chart_type) != chart.chart_type:
            continue
        result.append(chart)
    return result


def summarize_pptx(path: str | Path) -> dict[str, Any]:
    shapes = extract_shapes(path)
    charts = extract_charts(path)
    return {
        "path": str(path),
        "slide_count": slide_count(path),
        "slides": [
            {"slide": slide, "text": texts}
            for slide, texts in sorted(extract_text_by_slide(path).items())
        ],
        "shape_count": len(shapes),
        "chart_count": len(charts),
    }
