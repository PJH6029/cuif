# CUIF Evaluation Report: Annotated dashboard layout repair deck

- Task: `annotated_layout_repair_deck`
- Score: 57.00 / 57.00 (100.0%)
- Status counts: `{'pass': 26}`
- Blocked checks: none
- Preservation/regression failures: none

## Per-turn scores

| Turn | Earned | Possible | Score | Status counts |
| --- | ---: | ---: | ---: | --- |
| turn1 | 27.00 | 27.00 | 100.0% | `{'pass': 12}` |
| final | 30.00 | 30.00 | 100.0% | `{'pass': 14}` |

## Point distribution

- Thesis-heavy points: 45.00 / 53.00 (84.9%)
- Threshold: 60%; meets threshold: `True`
- Excluded points: 4.00 (`file_exists`, `pptx_slide_count`, and diagnostic preview checks)
- Buckets: `{'boilerplate': 4.0, 'content_source': 8.0, 'diagnostic': 0.0, 'layout_template_style': 22.0, 'preservation_regression': 23.0}`

## Checks

| Turn | Check | Evaluator | Status | Points | Message |
| --- | --- | --- | --- | ---: | --- |
| turn1 | taska_t1_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/turn1/result.pptx |
| turn1 | taska_t1_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 4 matched expected 4 |
| turn1 | taska_t1_core_texts | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| turn1 | taska_t1_checkout_top_left | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | taska_t1_backlog_top_center | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | taska_t1_fatigue_top_right | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | taska_t1_trend_panel_region | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| turn1 | taska_t1_risk_lower_right | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| turn1 | taska_t1_slide1_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| turn1 | taska_t1_slide3_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| turn1 | taska_t1_slide4_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| turn1 | taska_t1_rendered_review | rendered_layout_review | pass | 0.00/0.00 | Rendered preview generated for layout review |
| final | taska_final_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/final/result.pptx |
| final | taska_final_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 4 matched expected 4 |
| final | taska_final_title_style | pptx_style_check | pass | 4.00/4.00 | Style check passed |
| final | taska_final_handoff_texts | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| final | taska_final_caption_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| final | taska_final_action_owners_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| final | taska_final_risk_lower_right | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| final | taska_final_trend_layout_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| final | taska_final_checkout_layout_preserved | pptx_preservation_diff | pass | 2.00/2.00 | Protected content/layout preserved |
| final | taska_final_slide1_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| final | taska_final_slide3_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| final | taska_final_slide4_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| final | taska_optional_llm_repair_judge | llm_text_rubric | pass | 0.00/0.00 | Slide 2 contains the required repaired elements in text form: a top metric row with three metrics, a trend panel description, a lower-right checkout latency hotspot/callout, the caption, and the action owner list. Non-target slides 1, 3, and 4 appear preserved with their invariant text unchanged. Minor uncertainty remains because the summary is text-only and does not fully prove spatial layout dominance/positioning, but the content strongly matches the annotated repair requirements. |
| final | taska_optional_vlm_layout_judge | vlm_layout_rubric | pass | 0.00/0.00 | Slide 2 meets the layout requirements: the three metric cards are aligned across the top row, the service health trend panel occupies the large left-middle area, and the checkout latency callout is positioned in the lower-right. Protected slides 1, 3, and 4 appear unchanged in content and structure, with invariant text preserved. Minor score reduction only because exact pixel-perfect comparison to the annotated reference is not available from the summary alone, but the rendered result clearly satisfies the rubric. |

## Review assets

- **seed deck** `package.seed`: rendered (task/artifacts/seed.pptx)
- **turn 1 gold** `package.gold_turn1`: rendered (task/artifacts/gold/turn1.pptx)
- **turn 1 output** `run.outputs.turn1.result`: rendered (outputs/turn1/result.pptx)
- **final gold** `package.gold_final`: rendered (task/artifacts/gold/final.pptx)
- **final output** `run.outputs.final.result`: rendered (outputs/final/result.pptx)
