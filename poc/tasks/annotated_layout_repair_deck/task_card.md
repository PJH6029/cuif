# Task Card: Annotated Layout Repair Deck

Task topic: Annotated screenshot layout repair with non-target preservation.

Real-world scenario: A reliability operations team has an editable dashboard deck whose main dashboard slide drifted away from an annotated screenshot/layout reference. The agent must repair only the target slide, follow visual annotations, and preserve non-target slides across a later executive-handoff revision.

User goal: Repair slide 2 from concrete visual annotations and then add final handoff styling/content without regressing the repaired layout or collateral-damaging protected slides.

Primary output: PPTX deck.

Seed artifact contents:
- Slide 1: protected context slide with `Do not edit: Task A context invariant`.
- Slide 2: messy editable reliability dashboard with off-grid metric tiles, small trend panel, and misplaced risk callout.
- Slide 3: protected runbook evidence appendix with `Do not edit: runbook evidence invariant`.
- Slide 4: protected benchmark controls with `Do not edit: annotated repair benchmark invariant`.

Turn 1 request:
- Use `annotated_repair_reference.svg`, `slide2_seed_screenshot.png`, and `repair_notes.txt`.
- Align the three metric tiles across the top row.
- Expand `Service health trend` into the large left-middle panel.
- Move `Hotspot: checkout latency` to the lower-right callout.
- Preserve slides 1, 3, and 4 exactly.

Final turn request:
- Restyle the slide-2 title to CUIF blue #1F4E79, bold, 32 pt.
- Add a caption below the trend panel and an `Action owners` rail.
- Preserve the turn-1 repaired trend/metric layout plus slides 1, 3, and 4.

Protected content/regions:
- Slides 1, 3, and 4 are non-target protected slides.
- Final turn locks the repaired `Service health trend` and `Checkout SLA 97.2%` regions against turn 1.

Multimodal/source inputs:
- `artifacts/inputs/annotated_repair_reference.svg` — visual target zones and repair annotations.
- `artifacts/inputs/slide2_seed_screenshot.png` — messy source-state screenshot.
- `artifacts/inputs/repair_notes.txt` — textual repair and preservation notes.

What should be graded deterministically:
- Required editable text and slide count.
- Target-region placement with `pptx_bbox_region`.
- Final title style with `pptx_style_check`.
- Non-target and turn-regression preservation with `pptx_preservation_diff`.

What should be judged visually or semantically:
- VLM/layout review should inspect rendered previews against the annotated reference for top-row alignment, trend-panel dominance, lower-right callout placement, and lack of protected-slide changes.

Point budget by capability bucket:
- Boilerplate: 4 points (`file_exists`, `pptx_slide_count`).
- Content/source: 8 points (`pptx_text_contains`).
- Layout/template/style: 22 points (`pptx_bbox_region`, `pptx_style_check`).
- Preservation/regression: 23 points (`pptx_preservation_diff`).
- Diagnostic-only rendered/VLM/LLM checks: 0 points.

Evaluator adequacy verdict: Existing deterministic PPTX evaluators are sufficient for the scored target-region, style, preservation, and regression claims. VLM review remains diagnostic and is required as evidence, not as the scored source of truth.

Negative shortcut case: The seed/unrepaired fixture and any screenshot-only replacement should lose credit because required editable text, shape bounding boxes, style runs, and turn-regression selectors must be present as PPTX objects.
