# Task Card: native_chart_style_deck

## Scenario
A support operations lead needs a small executive PowerPoint deck that turns cross-file capacity data into a native editable chart and then applies a visual style/layout reference.

## Task ID
`native_chart_style_deck`

## Visual/style/layout assets
- `artifacts/inputs/layout_reference.svg` defines the slide-1 chart zone, insight strip, badge, and right observation rail.
- `artifacts/inputs/style_reference.svg` defines the CUIF blue title, cream canvas, rail styling, and chart color expectations.
- Both assets are referenced directly in turn instructions.

## Source data inputs
- `artifacts/inputs/source_metrics.xlsx` contains quarterly ticket demand and staffed capacity values plus provenance.
- `artifacts/inputs/source_metrics.csv` mirrors the data for agents that prefer text-like data extraction.
- `artifacts/inputs/analyst_notes.txt` identifies the key Q4 capacity gap and required audit wording.

## Turns
1. `turn1`: create a 3-slide support capacity deck from the source data and layout reference, including a native clustered column chart named `support_capacity_clustered_chart`.
2. `final`: apply the style reference, preserve the native chart data and source audit, add an insight strip/badge/right rail, and preserve the protected slide.

## Protected regions and turn-regression targets
- Slide 3 contains `Do not edit: native chart package invariant` and is protected from the seed onward.
- Final turn preserves slide 2 exactly from turn 1.
- Final turn preserves the chart data created in turn 1.

## Deterministic evaluators
- `pptx_chart_data` proves the target is a native editable PowerPoint chart and validates categories/series/values.
- `pptx_bbox_region` checks title, chart, badge, and right-rail layout regions.
- `pptx_style_check` checks final title typography/color.
- `pptx_preservation_diff` checks protected slide/source audit preservation.
- `pptx_image_count` with zero images on slide 1 penalizes screenshot-only chart shortcuts.

## Point budget by capability bucket
- Boilerplate: `file_exists`, `pptx_slide_count` only.
- Content/source: required text and audit values.
- Layout/style/native/preservation: chart data, no-raster shortcut checks, bbox checks, title style, and preservation diffs. Target share is above 60% excluding boilerplate and diagnostic preview checks.

## Known evaluator blind spots
- Chart visual colors are described in the style reference and gold deck but not deterministically scored beyond native chart data and layout.
- `pptx_style_check` verifies title text style only; it does not inspect chart series colors.

## Negative shortcut case
A flattened screenshot of the chart should fail `pptx_chart_data` because no native chart is present. A slide-1 screenshot fallback is also penalized by `pptx_image_count` expecting zero images on slide 1.

## Evaluator additions
None required; existing PPTX evaluators are sufficient for this package.
