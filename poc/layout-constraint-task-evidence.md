# Layout-constraint task package evidence

Date: 2026-05-04
Branch: `codex/poc-layout-constraint`
Team: `implement-the-layout-constrain`

This note summarizes the leader-side final integration review for the new layout/template-constrained PPTX task packages. Existing legacy flagship task directories were left untouched.

## Packages

| Task | Package path | Core thesis target | Mock score | Thesis-heavy share |
| --- | --- | --- | ---: | ---: |
| A | `poc/tasks/annotated_layout_repair_deck` | Annotated visual layout repair + protected-content preservation | 57/57 | 45/53 (84.9%) |
| B | `poc/tasks/public_template_compliance_deck` | Strict template/style/brand compliance with concrete visual assets | 66/66 | 52/62 (83.9%) |
| C | `poc/tasks/native_chart_style_deck` | Cross-file data-to-deck task with native editable PowerPoint chart | 71/71 | 48/67 (71.6%) |

## Worker-1 rerun/fix pass

Worker-1 reran the layout-constraint implementation against the PRD/test spec and integrated two read-only subagent critiques:

- Added explicit review comparison targets to Tasks B and C so their reports render seed, turn-1 gold, turn-1 output, final gold, and final output like Task A.
- Tightened Task B's final-turn regression coverage with scored `pptx_preservation_diff` checks for slide-1 status-card and footer geometry against the turn-1 output.
- Kept VLM checks optional/diagnostic in the manifests because the live OAuth endpoint can run the checks but currently rejects local data-URL/localhost image delivery; mandatory multimodal review is therefore recorded as runtime evidence/attempt logs rather than a deterministic package gate.

Fresh evidence logs from this rerun:

- `poc/tasks/annotated_layout_repair_deck/evidence/worker1_validation_20260504.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker1_postpatch_validation_20260504.log`
- `poc/tasks/native_chart_style_deck/evidence/worker1_postpatch_validation_20260504.log`
- `poc/tasks/annotated_layout_repair_deck/evidence/worker1_live_judge_dataurl_20260504.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker1_live_judge_dataurl_20260504.log`
- `poc/tasks/native_chart_style_deck/evidence/worker1_live_judge_dataurl_20260504.log`
- `poc/tasks/annotated_layout_repair_deck/evidence/worker1_codex_baseline_20260504.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker1_codex_baseline_20260504.log`
- `poc/tasks/native_chart_style_deck/evidence/worker1_codex_baseline_20260504.log`

## Final deterministic validation

Run from repo root:

```bash
uv run cuif-eval validate poc/tasks/annotated_layout_repair_deck/manifest.yaml --skip-judges
uv run cuif-eval point-distribution poc/tasks/annotated_layout_repair_deck/manifest.yaml --fail-below-threshold
uv run cuif-eval run --task poc/tasks/annotated_layout_repair_deck --adapter mock --out output/runs/annotated_layout_repair_deck_mock --skip-judges

uv run cuif-eval validate poc/tasks/public_template_compliance_deck/manifest.yaml --skip-judges
uv run cuif-eval point-distribution poc/tasks/public_template_compliance_deck/manifest.yaml --fail-below-threshold
uv run cuif-eval run --task poc/tasks/public_template_compliance_deck --adapter mock --out output/runs/public_template_compliance_deck_mock --skip-judges

uv run cuif-eval validate poc/tasks/native_chart_style_deck/manifest.yaml --skip-judges
uv run cuif-eval point-distribution poc/tasks/native_chart_style_deck/manifest.yaml --fail-below-threshold
uv run cuif-eval run --task poc/tasks/native_chart_style_deck --adapter mock --out output/runs/native_chart_style_deck_mock --skip-judges
```

Observed result: all three manifests validate, all three point distributions pass the 60% thesis-heavy threshold, and all three mock runs score 100% with no non-diagnostic nonpass checks.

## Live judge evidence

Leader ran live judge attempts with:

```bash
npx -y openai-oauth --models gpt-5.4 --port 10536
uv run cuif-eval run --task <task> --adapter mock --out output/runs/<task>_judge \
  --judge-base-url http://127.0.0.1:10536/v1 \
  --judge-model gpt-5.4 \
  --judge-image-url-base http://127.0.0.1:8766/<task>_judge \
  --refresh-judge-cache
```

Evidence logs:
- `poc/tasks/annotated_layout_repair_deck/evidence/live_judge_leader.log`
- `poc/tasks/public_template_compliance_deck/evidence/live_judge_leader.log`
- `poc/tasks/native_chart_style_deck/evidence/live_judge_leader.log`

Outcome: deterministic scores remained 100%. Task A's LLM judge passed. Optional VLM judges were attempted but upstream image fetching could not download localhost URLs (`407`), so the optional zero-point VLM checks are recorded as live-attempt errors rather than deterministic scoring blockers. Data-URL retry logs are also stored in each task's `evidence/` directory. Worker-1 reran the data-URL path through `npx -y openai-oauth --models gpt-5.4 --port 10641`; the endpoint became ready and each evaluator run completed with a 100% deterministic score, while each optional VLM check logged `URL scheme must be http or https, got data:`.

## Codex baseline evidence

Baseline command shape:

```bash
uv run cuif-eval run-and-evaluate --task <task> --bundle output/bundles/<task>_codex \
  --run output/runs/<task>_codex --agent codex-exec --overwrite-bundle --skip-judges
```

Evidence logs:
- `poc/tasks/annotated_layout_repair_deck/evidence/codex_baseline_leader.log` — actual `codex-exec` invocation entered the task and rendered seed/reference assets, then timed out at 420s.
- `poc/tasks/public_template_compliance_deck/evidence/codex_baseline_bounded_leader.log` — actual `codex-exec` invocation timed out at 90s.
- `poc/tasks/native_chart_style_deck/evidence/codex_baseline_bounded_leader.log` — actual `codex-exec` invocation timed out at 90s.

These baseline attempts are intentionally retained as construction-time evidence that the tasks were not only evaluated against gold/mock outputs. They did not produce complete scored baseline reports within the bounded runtime.

## Regression/test evidence

```bash
uv run pytest
```

Observed result: `54 passed in 3.89s`.

Legacy directory guard checked against the pre-team branch point (`a7ea99e`): no diffs under:
- `poc/tasks/incident_response_annotated_deck`
- `poc/tasks/renewable_power_briefing_deck`
- `poc/tasks/transformer_paper_review_deck`
