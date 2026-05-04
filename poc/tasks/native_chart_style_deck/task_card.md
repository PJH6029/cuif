# Task Card: Native Chart Style Deck

Task topic: Cross-file data-to-deck with native editable chart and visual style/layout constraints.

Real-world scenario: A support operations lead needs an executive PowerPoint deck that converts capacity-forecast data from XLSX/CSV/text notes into a native editable chart, then applies a visual reference without flattening the chart into a screenshot.

User goal: Create a three-slide PPTX deck with a native clustered column chart from source data, then revise it with a style reference while preserving chart data, source audit evidence, and protected slides.

Primary output: PPTX deck.

Seed artifact contents:
- Slide 1: planning context for support capacity forecast.
- Slide 2: rough source/audit placeholder.
- Slide 3: protected context slide with `Do not edit: native chart package invariant`.

Turn 1 request:
- Use `source_metrics.xlsx`, `source_metrics.csv`, `analyst_notes.txt`, and `layout_reference.svg`.
- Create a native editable PowerPoint clustered column chart named `support_capacity_clustered_chart`.
- Use categories Q1--Q4 and exact `Ticket demand` / `Staffed capacity` series values.
- Add a source-audit slide with required workbook/audit strings.
- Preserve slide 3 exactly.

Final turn request:
- Use `style_reference.svg`.
- Style the title to CUIF blue #1F4E79, bold, 34 pt.
- Preserve native chart data and the chart-left layout.
- Add top-right badge, right observation rail, and insight strip.
- Preserve slide 2 and slide 3 exactly from turn 1.

Protected content/regions:
- Slide 3 sentinel is protected from the seed onward.
- Final turn preserves slide 2 source audit from turn 1.
- Final turn revalidates the native chart data rather than trusting visible similarity.

Multimodal/source inputs:
- `artifacts/inputs/source_metrics.xlsx` and `source_metrics.csv` — source data.
- `artifacts/inputs/analyst_notes.txt` — data provenance and narrative instructions.
- `artifacts/inputs/layout_reference.svg` — chart, badge, rail, and insight-strip zones.
- `artifacts/inputs/style_reference.svg` — title, series-color, cream canvas, and rail style guidance.

What should be graded deterministically:
- Native chart existence/type/categories/series/values with `pptx_chart_data`.
- Screenshot shortcut penalty with `pptx_image_count` on slide 1.
- Title/chart/badge/rail placement with `pptx_bbox_region`.
- Final title style with `pptx_style_check`.
- Source audit/protected slide preservation with `pptx_preservation_diff`.

What should be judged visually or semantically:
- VLM/layout review should inspect rendered previews for dashboard hierarchy, chart readability, right-rail placement, badge/insight-strip placement, and absence of screenshot-only shortcuts.

Point budget by capability bucket:
- Boilerplate: 4 points (`file_exists`, `pptx_slide_count`).
- Content/source: 15 points (`pptx_text_contains`).
- Native editability: 15 points (`pptx_chart_data`).
- Layout/template/style: 21 points (`pptx_bbox_region`, `pptx_style_check`).
- Screenshot shortcut/native-object guard: 4 points (`pptx_image_count`).
- Preservation/regression: 12 points (`pptx_preservation_diff`).
- Diagnostic-only rendered/VLM checks: 0 points.

Evaluator adequacy verdict: Existing PPTX evaluators are sufficient because Task C chooses a native chart path. `pptx_chart_data` proves editability and source fidelity, while `pptx_image_count` now runs independently of chart-data success so a screenshot-only chart loses explicit shortcut-guard credit instead of being merely blocked.

Negative shortcut case: A rasterized chart screenshot fixture should fail `pptx_chart_data` and `pptx_image_count` even if it looks visually plausible.
