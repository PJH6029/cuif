# Layout-Constraint A/B/C Mandatory Multimodal Review

Date: 2026-05-04
Reviewer: worker-3
Scope: Task 5, mandatory multimodal/VLM critique of new A/B/C visual inputs, seed/gold PPTX previews, and multimodal assets. Legacy task directories were not edited.

## Reviewed packages

| Package | Archetype | Verdict | Revision request |
|---|---|---|---|
| `poc/tasks/annotated_layout_repair_deck` | Task A — annotated screenshot layout repair | **FAIL** | Fix trend-line/text overlap on slide 2 in turn 1 and final gold decks. |
| `poc/tasks/public_template_compliance_deck` | Task B — strict template/style compliance | **PASS** | None from multimodal review. |
| `poc/tasks/native_chart_style_deck` | Task C — cross-file native chart style deck | **PASS** | None from multimodal review. |

## Repo-level evidence assets

- Cross-task contact sheet: `poc/layout_constraint_multimodal_review_contact_sheet.png`
- Data URL VLM response: `poc/layout_constraint_multimodal_review_vlm_response.json`
- Data URL curl stderr: `poc/layout_constraint_multimodal_review_vlm_curl.err`
- HTTP image VLM response: `poc/layout_constraint_multimodal_review_vlm_http_response.json`
- HTTP image curl stderr: `poc/layout_constraint_multimodal_review_vlm_http_curl.err`
- OAuth server logs:
  - `poc/layout_constraint_multimodal_review_oauth_server.log`
  - `poc/layout_constraint_multimodal_review_oauth_http_server.log`
  - `poc/layout_constraint_multimodal_review_contact_http_server.log`

## Package-local evidence notes

- `poc/tasks/annotated_layout_repair_deck/evidence/multimodal_review/review.md`
- `poc/tasks/public_template_compliance_deck/evidence/multimodal_review/review.md`
- `poc/tasks/native_chart_style_deck/evidence/multimodal_review/review.md`

Each package also contains contact sheets for visual inputs, seed previews, gold turn 1 previews, gold final previews, and per-slide rendered PNGs under `evidence/multimodal_review/`.

## gpt-5.4 VLM transport evidence

`npx --yes openai-oauth --port <port> --models gpt-5.4` succeeded and exposed `gpt-5.4` via `/v1/models`.

Image submission attempts:

1. Data URL image payload to `/v1/chat/completions` failed with: `URL scheme must be http or https, got data:`.
2. HTTP-served local contact sheet payload failed with: `Error while downloading http://127.0.0.1:8765/poc/layout_constraint_multimodal_review_contact_sheet.png. Upstream status code: 407.`

Conclusion: the model endpoint was available, but image transport was blocked. Per the task instruction, contact sheets were created and preserved for orchestrator multimodal inspection.

## Deterministic point-distribution review

Excluding `file_exists`, `pptx_slide_count`, and diagnostic-only `rendered_layout_review`:

| Package | Non-boilerplate points | Thesis-heavy points | Thesis-heavy share |
|---|---:|---:|---:|
| `annotated_layout_repair_deck` | 53 | 45 | 84.9% |
| `public_template_compliance_deck` | 54 | 44 | 81.5% |
| `native_chart_style_deck` | 67 | 52 | 77.6% |

All packages satisfy the PRD/test-spec threshold by point distribution, but Task A still needs the visual overlap fix before final multimodal acceptance.

## Multimodal findings

### Task A — annotated layout repair

Pass:

- Annotated visual reference and seed screenshot are concrete and instruction-relevant.
- Gold decks visibly implement top-row metric alignment, expanded trend panel, lower-right hotspot, final caption, and action-owner rail.
- Protected slides are visually stable.

Fail / revision request:

- The slide 2 trend-line graphic crosses the `Service health trend` title/body text in both turn 1 and final gold previews. This is an obvious visual overlap in the core edited region.
- Request: move the line lower or move the title/body copy so the chart stroke no longer intersects text, then regenerate gold previews and preserve all current deterministic check targets.

### Task B — public template compliance

Pass:

- Visual/style inputs are concrete and gold decks visibly follow the navy header/footer, teal section band, seal placement, grid/cards, lower panels, and compliance-table template.
- No obvious rendered overlap or template contradiction was observed.

Revision request: none.

### Task C — native chart style deck

Pass:

- Visual inputs specify chart, badge, observation rail, insight strip, title color, and series styling.
- Gold decks visibly instantiate the left chart region, top-right badge, right observation rail, insight strip, workbook audit, and protected context slide.
- Visual review does not show a screenshot-only shortcut; keep deterministic `pptx_chart_data` and `pptx_image_count` checks as enforcement.

Revision request: none.

## Worker-3 completion verification rerun

Fresh verification run from worker-3 on 2026-05-04:

- `uv run cuif-eval validate poc/tasks/annotated_layout_repair_deck/manifest.yaml --skip-judges` → PASS (`OK: annotated_layout_repair_deck (2 turns)`).
- `uv run cuif-eval validate poc/tasks/public_template_compliance_deck/manifest.yaml --skip-judges` → PASS (`OK: public_template_compliance_deck (2 turns)`).
- `uv run cuif-eval validate poc/tasks/native_chart_style_deck/manifest.yaml --skip-judges` → PASS (`OK: native_chart_style_deck (2 turns)`).
- `uv run cuif-eval run --task poc/tasks/annotated_layout_repair_deck --adapter mock --out output/runs/annotated_layout_repair_deck_worker3_mock --skip-judges` → PASS (`57.00/57.00`).
- `uv run cuif-eval run --task poc/tasks/public_template_compliance_deck --adapter mock --out output/runs/public_template_compliance_deck_worker3_mock --skip-judges` → PASS (`58.00/58.00`).
- `uv run cuif-eval run --task poc/tasks/native_chart_style_deck --adapter mock --out output/runs/native_chart_style_deck_worker3_mock --skip-judges` → PASS (`71.00/71.00`).
- `uv run pytest` → PASS (`54 passed`).
- `uv run python -m compileall -q src tests` → PASS (no output).

Completion note: this rerun confirms the package manifests and mock outputs are valid, but the multimodal verdict remains **Task A FAIL / revision requested** because the rendered trend-line/text overlap is a visual-quality issue not caught by current deterministic checks.
