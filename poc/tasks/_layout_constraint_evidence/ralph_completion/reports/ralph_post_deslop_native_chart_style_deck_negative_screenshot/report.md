# CUIF Evaluation Report: Native chart style deck from cross-file capacity data

- Task: `native_chart_style_deck`
- Score: 40.00 / 71.00 (56.3%)
- Status counts: `{'pass': 15, 'fail': 5, 'blocked': 2, 'skipped': 1}`
- Blocked checks: native_chart_t1_chart_region, native_chart_final_chart_left_region
- Preservation/regression failures: native_chart_t1_protected_slide_preserved

## Per-turn scores

| Turn | Earned | Possible | Score | Status counts |
| --- | ---: | ---: | ---: | --- |
| turn1 | 12.00 | 30.00 | 40.0% | `{'pass': 6, 'fail': 3, 'blocked': 1}` |
| final | 28.00 | 41.00 | 68.3% | `{'pass': 9, 'fail': 2, 'blocked': 1, 'skipped': 1}` |

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
| turn1 | native_chart_t1_chart_data | pptx_chart_data | fail | 0.00/8.00 | No PPTX chart matched selector {'slide': 1, 'name': 'support_capacity_clustered_chart'} |
| turn1 | native_chart_t1_chart_region | pptx_bbox_region | blocked | 0.00/4.00 | Blocked by failed/skipped dependencies: native_chart_t1_chart_data |
| turn1 | native_chart_t1_title_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | native_chart_t1_source_audit_values | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| turn1 | native_chart_t1_no_slide1_raster_shortcut | pptx_image_count | fail | 0.00/2.00 | Found 1 images; expected exactly 0 |
| turn1 | native_chart_t1_protected_slide_preserved | pptx_preservation_diff | fail | 0.00/4.00 | Preservation differences detected |
| turn1 | native_chart_t1_rendered_review | rendered_layout_review | pass | 0.00/0.00 | Rendered preview generated for layout review |
| final | native_chart_final_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/final/result.pptx |
| final | native_chart_final_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 3 matched expected 3 |
| final | native_chart_final_title_style | pptx_style_check | pass | 5.00/5.00 | Style check passed |
| final | native_chart_final_chart_data_preserved | pptx_chart_data | fail | 0.00/7.00 | No PPTX chart matched selector {'slide': 1, 'name': 'support_capacity_clustered_chart'} |
| final | native_chart_final_chart_left_region | pptx_bbox_region | blocked | 0.00/4.00 | Blocked by failed/skipped dependencies: native_chart_final_chart_data_preserved |
| final | native_chart_final_badge_region | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| final | native_chart_final_rail_texts | pptx_text_contains | pass | 4.00/4.00 | All required PPTX text was present |
| final | native_chart_final_rail_region | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| final | native_chart_final_insight_text | pptx_text_contains | pass | 3.00/3.00 | All required PPTX text was present |
| final | native_chart_final_no_slide1_raster_shortcut | pptx_image_count | fail | 0.00/2.00 | Found 1 images; expected exactly 0 |
| final | native_chart_final_source_audit_preserved | pptx_preservation_diff | pass | 4.00/4.00 | Protected content/layout preserved |
| final | native_chart_final_protected_slide_preserved | pptx_preservation_diff | pass | 4.00/4.00 | Protected content/layout preserved |
| final | optional_vlm_native_chart_layout_judge | vlm_layout_rubric | skipped | 0.00/0.00 | Judge checks skipped by configuration |

## Review assets

- **seed deck** `package.seed`: rendered (task/artifacts/seed.pptx)
- **turn 1 gold** `package.gold_turn1`: rendered (task/artifacts/gold/turn1.pptx)
- **turn 1 output** `run.outputs.turn1.result`: rendered (outputs/turn1/result.pptx)
- **final gold** `package.gold_final`: rendered (task/artifacts/gold/final.pptx)
- **final output** `run.outputs.final.result`: rendered (outputs/final/result.pptx)
