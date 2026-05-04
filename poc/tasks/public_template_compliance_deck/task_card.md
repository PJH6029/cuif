# Task Card: Public Template Compliance Deck

Task topic: Strict public-sector/corporate template compliance deck

Real-world scenario: A regional grants office has a locked public briefing template. Staff need an editable PowerPoint briefing filled from a short status brief while preserving explicit margins, typography, section bands, alignment, colors, footer language, and a protected legal notice region.

User goal: Turn a rough seed deck into a polished two-slide Metro Civic Grants briefing that follows the supplied template/style references exactly enough to be visually and deterministically checked, then revise the final deck without damaging prior template-constrained work.

Primary output: PPTX deck

Seed artifact contents:
- Slide 1: rough unstyled content blocks for program status, funding, timeline, risks, and a protected legal notice.
- Slide 2: rough unstyled compliance-monitoring content and a protected audit-footer sentinel.

Turn 1 request:
- Apply the Metro Civic public template to two slides using the provided style reference, layout grid, seal, and template rules.
- Add required header, footer, section band, title, status cards, and timeline/table elements.
- Preserve protected legal/audit text exactly.

Final turn request:
- Revise slide 1 by adding an oversight callout in the approved lower-right region.
- Restyle the slide 1 title and slide 2 section header to final template colors/weights.
- Preserve the turn-1 card layout, footer language, slide 2 table/header layout, and all protected text.

Protected content/regions:
- Slide 1 protected legal notice: `Protected legal notice: FY26 allocations remain preliminary until council adoption.`
- Slide 2 protected audit footer: `Do not edit: Metro Civic audit trail invariant.`
- Final turn preserves slide 2 compliance content from turn 1.

Multimodal/source inputs:
- `style_reference.svg` visual template showing header/footer bands, colors, typography notes, and protected region.
- `layout_grid.svg` visual grid showing normalized margins, card/table zones, and final-turn callout zone.
- `metro_civic_seal.png` required seal/logo to embed in the deck.
- `template_rules.txt` textual public-template rules.

What should be graded deterministically:
- Required text and slide count.
- Title/header/footer/card/table/callout placement with `pptx_bbox_region`.
- Required typography/color/bold settings with `pptx_style_check`.
- Required seal image match and placement with `pptx_image_match`.
- Protected text and turn-regression preservation with `pptx_preservation_diff`.

What should be judged visually or semantically:
- Optional VLM rubric checks whether the rendered deck follows the public-sector template hierarchy, margins, colors, protected regions, and alignment without overlap.

Point budget by capability bucket:
- Boilerplate: 4 points (`file_exists`, `pptx_slide_count`).
- Content/source: 10 points (`pptx_text_contains`).
- Layout/template/style/image fidelity: 35 points (`pptx_bbox_region`, `pptx_style_check`, `pptx_image_match`).
- Preservation/regression: 9 points (`pptx_preservation_diff`).
- Diagnostic-only rendered/VLM checks: 0 points.

Evaluator adequacy verdict: Existing evaluators are sufficient for this Task B package. Style fidelity is covered by targeted text style checks; template/layout fidelity is covered by bbox checks on header/footer/cards/table/callout plus seal image match. Remaining aesthetic nuance is documented as a VLM diagnostic blind spot rather than converted into content-heavy scoring.

Negative shortcut case: A flattened screenshot-only deck or arbitrary styling should fail because the seal must be an embedded matching image, text runs must expose required font style/color/size, and required text boxes must sit in normalized template regions.
