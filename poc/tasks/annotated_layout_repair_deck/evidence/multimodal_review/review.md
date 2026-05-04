# Multimodal Review — Task A: annotated layout repair

Date: 2026-05-04
Reviewer: worker-3

## Evidence assets

- Input asset contact sheet: `poc/tasks/annotated_layout_repair_deck/evidence/multimodal_review/input_assets_montage.png`
- Seed preview contact sheet: `poc/tasks/annotated_layout_repair_deck/evidence/multimodal_review/seed_montage.png`
- Gold turn 1 contact sheet: `poc/tasks/annotated_layout_repair_deck/evidence/multimodal_review/gold_turn1_montage.png`
- Gold final contact sheet: `poc/tasks/annotated_layout_repair_deck/evidence/multimodal_review/gold_final_montage.png`
- Per-slide rendered previews: `poc/tasks/annotated_layout_repair_deck/evidence/multimodal_review/rendered/`

## VLM transport attempt

- `npx --yes openai-oauth --port 10543 --models gpt-5.4` exposed `gpt-5.4` successfully.
- Data URL image payload failed with: `URL scheme must be http or https, got data:`.
- HTTP-served contact sheet payload failed with upstream image-download status `407`.
- Because transport blocked image access, the rendered previews and contact sheets above are prepared for orchestrator multimodal inspection.

## Visual review verdict

**Verdict: FAIL — revision requested before final acceptance.**

Pass findings:

- The package includes concrete visual inputs: an annotated repair reference and seed screenshot.
- The seed visibly contains the messy source dashboard, and the gold decks visibly move the metric tiles into a top row, expand the service health panel, and place the hotspot callout in the lower-right region.
- Protected slides 1, 3, and 4 remain visually stable across seed, turn 1, and final.

Fail finding / revision request:

- On slide 2 in both `gold/turn1.pptx` and `gold/final.pptx`, the trend-line graphic intersects/overlaps the `Service health trend` title/body text in the large trend panel. This weakens the visual-instruction grounding claim because the annotated reference implies a readable trend panel, not a line drawn through the label.

Concrete revision request:

1. Reposition the trend line lower or move the title/body copy above/left of the line so no chart stroke crosses text.
2. Re-render `gold_turn1_montage.png` and `gold_final_montage.png` after the fix.
3. Keep the existing top-row metrics, lower-right hotspot, action owners rail, caption, and protected-slide preservation unchanged.
