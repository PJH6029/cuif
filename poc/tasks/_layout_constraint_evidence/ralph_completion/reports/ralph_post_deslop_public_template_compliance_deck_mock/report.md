# CUIF Evaluation Report: Metro Civic public template compliance deck

- Task: `public_template_compliance_deck`
- Score: 66.00 / 66.00 (100.0%)
- Status counts: `{'pass': 28, 'skipped': 1}`
- Blocked checks: none
- Preservation/regression failures: none

## Per-turn scores

| Turn | Earned | Possible | Score | Status counts |
| --- | ---: | ---: | ---: | --- |
| turn1 | 33.00 | 33.00 | 100.0% | `{'pass': 15}` |
| final | 33.00 | 33.00 | 100.0% | `{'pass': 13, 'skipped': 1}` |

## Point distribution

- Thesis-heavy points: 52.00 / 62.00 (83.9%)
- Threshold: 60%; meets threshold: `True`
- Excluded points: 4.00 (`file_exists`, `pptx_slide_count`, and diagnostic preview checks)
- Buckets: `{'boilerplate': 4.0, 'content_source': 10.0, 'diagnostic': 0.0, 'layout_template_style': 35.0, 'preservation_regression': 17.0}`

## Checks

| Turn | Check | Evaluator | Status | Points | Message |
| --- | --- | --- | --- | ---: | --- |
| turn1 | metro_t1_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/turn1/result.pptx |
| turn1 | metro_t1_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 2 matched expected 2 |
| turn1 | metro_t1_required_texts | pptx_text_contains | pass | 5.00/5.00 | All required PPTX text was present |
| turn1 | metro_t1_seal_match_slide1 | pptx_image_match | pass | 3.00/3.00 | Image match check passed |
| turn1 | metro_t1_title_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | metro_t1_section_band_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | metro_t1_program_card_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | metro_t1_funding_card_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | metro_t1_timeline_card_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | metro_t1_compliance_table_region | pptx_bbox_region | pass | 2.00/2.00 | Shape bbox is inside requested region |
| turn1 | metro_t1_title_style | pptx_style_check | pass | 3.00/3.00 | Style check passed |
| turn1 | metro_t1_footer_style | pptx_style_check | pass | 2.00/2.00 | Style check passed |
| turn1 | metro_t1_legal_notice_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| turn1 | metro_t1_audit_notice_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| turn1 | metro_t1_rendered_review | rendered_layout_review | pass | 0.00/0.00 | Rendered preview generated for layout review |
| final | metro_final_file_exists | file_exists | pass | 1.00/1.00 | File exists: outputs/final/result.pptx |
| final | metro_final_slide_count | pptx_slide_count | pass | 1.00/1.00 | Slide count 2 matched expected 2 |
| final | metro_final_required_texts | pptx_text_contains | pass | 5.00/5.00 | All required PPTX text was present |
| final | metro_final_title_style | pptx_style_check | pass | 4.00/4.00 | Style check passed |
| final | metro_final_section_header_style | pptx_style_check | pass | 3.00/3.00 | Style check passed |
| final | metro_final_callout_region | pptx_bbox_region | pass | 3.00/3.00 | Shape bbox is inside requested region |
| final | metro_final_seal_match_slide1 | pptx_image_match | pass | 2.00/2.00 | Image match check passed |
| final | metro_final_footer_style | pptx_style_check | pass | 3.00/3.00 | Style check passed |
| final | metro_final_program_card_layout_preserved | pptx_preservation_diff | pass | 2.00/2.00 | Protected content/layout preserved |
| final | metro_final_funding_card_layout_preserved | pptx_preservation_diff | pass | 2.00/2.00 | Protected content/layout preserved |
| final | metro_final_timeline_card_layout_preserved | pptx_preservation_diff | pass | 2.00/2.00 | Protected content/layout preserved |
| final | metro_final_slide1_footer_layout_preserved | pptx_preservation_diff | pass | 2.00/2.00 | Protected content/layout preserved |
| final | metro_final_slide2_preserved | pptx_preservation_diff | pass | 3.00/3.00 | Protected content/layout preserved |
| final | metro_final_optional_vlm_template_judge | vlm_layout_rubric | skipped | 0.00/0.00 | Judge checks skipped by configuration |

## Review assets

- **seed deck** `package.seed`: rendered (task/artifacts/seed.pptx)
- **turn 1 gold** `package.gold_turn1`: rendered (task/artifacts/gold/turn1.pptx)
- **turn 1 output** `run.outputs.turn1.result`: rendered (outputs/turn1/result.pptx)
- **final gold** `package.gold_final`: rendered (task/artifacts/gold/final.pptx)
- **final output** `run.outputs.final.result`: rendered (outputs/final/result.pptx)
