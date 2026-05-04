# Task Card: Annotated layout repair deck

## Scenario
A reliability operations team has an editable PowerPoint deck whose dashboard slide drifted away from an annotated screenshot/layout reference. The agent must repair only the target dashboard slide, follow concrete visual annotations, and preserve non-target slides across turns.

## Visual/layout assets
- `artifacts/inputs/slide2_seed_screenshot.png` shows the messy source state for slide 2.
- `artifacts/inputs/annotated_repair_reference.svg` marks the target top-row metrics, dominant left-middle trend panel, lower-right risk callout, and protected non-target boundary.
- `artifacts/inputs/repair_notes.txt` gives the exact textual instructions and protected sentinels.

## Turns
- `turn1`: repair slide 2 according to the annotated visual reference while preserving slides 1, 3, and 4 exactly.
- `final`: add executive handoff styling and a caption/owner list while preserving the turn-1 layout and non-target slides.

## Protected content and regression targets
- Slide 1 sentinel: `Do not edit: Task A context invariant`.
- Slide 3 sentinel: `Do not edit: runbook evidence invariant`.
- Slide 4 sentinel: `Do not edit: annotated repair benchmark invariant`.
- Final turn compares selected slide-2 regions against turn 1 using `pptx_preservation_diff` to catch layout regression.

## Evaluator adequacy matrix

| Thesis claim | Evaluators | Target point share | Blind spot | Owner verdict |
|---|---|---:|---|---|
| Annotated visual repair | `pptx_bbox_region`, optional `vlm_layout_rubric` | majority of scored checks | bbox cannot judge all aesthetics | Existing deterministic bbox checks are sufficient for target-region placement. |
| Non-target preservation | `pptx_preservation_diff` with exact slide text | major preservation slice | text-level exactness does not compare every visual pixel | Sufficient because protected slides are text-heavy sentinels. |
| Turn-regression safety | `pptx_preservation_diff` against `run.outputs.turn1.result` | final-turn scored checks | selected regions only | Sufficient because the key repaired panel and metric tile are protected. |

## Point distribution (manifest design)

Excluding boilerplate `file_exists`, `pptx_slide_count`, and diagnostic-only preview/judge checks, the manifest assigns most points to layout, preservation, style, and regression checks:

- `turn1`: 21/25 non-boilerplate points are layout/preservation = 84%.
- `final`: 24/28 non-boilerplate points are layout/style/preservation/regression = 85.7%.
- Overall: 45/53 non-boilerplate points are thesis-heavy = 84.9%.

## Negative shortcut case
A screenshot-only replacement of slide 2 may preserve visible pixels but should lose deterministic credit because the checks search for editable text boxes and shape bounding boxes, and final-turn regression checks compare PPTX shape regions.

## Evidence notes
Validation, smoke run, live judge attempt, and Codex baseline attempt are recorded in the worker completion report.
