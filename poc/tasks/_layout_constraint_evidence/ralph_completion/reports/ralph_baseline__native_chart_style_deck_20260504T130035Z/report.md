# CUIF Evaluation Report: Native chart style deck from cross-file capacity data

- Task: `native_chart_style_deck`
- Score: 63.00 / 71.00 (88.7%)
- Status counts: `{'pass': 20, 'fail': 2, 'skipped': 1}`
- Blocked checks: none
- Preservation/regression failures: none

## Per-turn scores

| Turn | Earned | Possible | Score | Status counts |
| --- | ---: | ---: | ---: | --- |
| turn1 | 26.00 | 30.00 | 86.7% | `{'pass': 9, 'fail': 1}` |
| final | 37.00 | 41.00 | 90.2% | `{'pass': 11, 'fail': 1, 'skipped': 1}` |

## Point distribution

- Thesis-heavy points: 48.00 / 67.00 (71.6%)
- Threshold: 60%; meets threshold: `True`
- Excluded points: 4.00 (`file_exists`, `pptx_slide_count`, and diagnostic preview checks)
- Buckets: `{'boilerplate': 4.0, 'content_source': 15.0, 'diagnostic': 0.0, 'layout_template_style': 21.0, 'native_editability': 15.0, 'other': 4.0, 'preservation_regression': 12.0}`

## Checks

| Turn | Check | Evaluator | Status | Points | Message |
| --- | --- | --- | --- | ---: | --- |
| turn1 | native_chart_t1_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/turn1/result.pptx |
| turn1 | native_chart_t1_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 3 matched expected 3 |
| turn1 | native_chart_t1_core_texts | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| turn1 | native_chart_t1_chart_data | pptx_chart_data | pass | 8.00/8.00 | Chart data check passed |
| turn1 | native_chart_t1_chart_region | pptx_bbox_region | fail | 0.00/4.00 | Shape bbox is outside requested region |
| turn1 | native_chart_t1_title_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | native_chart_t1_source_audit_values | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| turn1 | native_chart_t1_no_slide1_raster_shortcut | pptx_image_count | pass | 2.00/2.00 | Found 0 images; expected exactly 0 |
| turn1 | native_chart_t1_protected_slide_preserved | pptx_preservation_diff | pass | 4.00/4.00 | Protected content/layout preserved |
| turn1 | native_chart_t1_rendered_review | rendered_layout_review | pass | 0.00/0.00 | Rendered preview generated for layout review |
| final | native_chart_final_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/final/result.pptx |
| final | native_chart_final_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 3 matched expected 3 |
| final | native_chart_final_title_style | pptx_style_check | pass | 5.00/5.00 | Style check passed |
| final | native_chart_final_chart_data_preserved | pptx_chart_data | pass | 7.00/7.00 | Chart data check passed |
| final | native_chart_final_chart_left_region | pptx_bbox_region | fail | 0.00/4.00 | Shape bbox is outside requested region |
| final | native_chart_final_badge_region | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| final | native_chart_final_rail_texts | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| final | native_chart_final_rail_region | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| final | native_chart_final_insight_text | pptx_text_contains | pass | 3.00/3.00 | All required PPTX text was present |
| final | native_chart_final_no_slide1_raster_shortcut | pptx_image_count | pass | 2.00/2.00 | Found 0 images; expected exactly 0 |
| final | native_chart_final_source_audit_preserved | pptx_preservation_diff | pass | 4.00/4.00 | Protected content/layout preserved |
| final | native_chart_final_protected_slide_preserved | pptx_preservation_diff | pass | 4.00/4.00 | Protected content/layout preserved |
| final | optional_vlm_native_chart_layout_judge | vlm_layout_rubric | skipped | 0.00/0.00 | Judge checks skipped by configuration |

## Review assets

- **seed deck** `package.seed`: rendered (task/artifacts/seed.pptx)
- **turn 1 gold** `package.gold_turn1`: rendered (task/artifacts/gold/turn1.pptx)
- **turn 1 output** `run.outputs.turn1.result`: rendered (outputs/turn1/result.pptx)
- **final gold** `package.gold_final`: rendered (task/artifacts/gold/final.pptx)
- **final output** `run.outputs.final.result`: rendered (outputs/final/result.pptx)
