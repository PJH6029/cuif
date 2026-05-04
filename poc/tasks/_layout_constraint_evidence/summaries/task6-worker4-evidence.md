# Worker-4 Task 6 Evidence: Baseline and Live VLM Judge Attempts

Task 6 required non-skipped execution evidence for `openai-oauth`/`gpt-5.4` VLM transport and bounded `codex-exec` baselines for the three new layout-constraint packages. Legacy/reference task directories were not edited.

## Packages covered

- Task A: `poc/tasks/annotated_layout_repair_deck`
- Task B: `poc/tasks/public_template_compliance_deck`
- Task C: `poc/tasks/native_chart_style_deck`

## VLM / `openai-oauth` evidence

Shared timestamp: `20260504T113455Z`.

- `npx -y openai-oauth --host 127.0.0.1 --port 10541` started successfully and exposed `gpt-5.4`.
- Direct `gpt-5.4` data-URL image request was attempted and logged; endpoint returned `URL scheme must be http or https, got data:`.
- Direct `gpt-5.4` HTTPS image-URL request was attempted and succeeded with `pass=true` JSON.
- `uv run cuif-eval run --adapter mock --judge-base-url http://127.0.0.1:10541/v1 --judge-model gpt-5.4 --refresh-judge-cache` was run for A/B/C.

Package-local logs:

- `poc/tasks/annotated_layout_repair_deck/evidence/worker4_live_judge_dataurl_20260504T113455Z.log`
- `poc/tasks/annotated_layout_repair_deck/evidence/worker4_openai_oauth_probe_20260504T113455Z.log`
- `poc/tasks/annotated_layout_repair_deck/evidence/worker4_openai_oauth_https_probe_20260504T113455Z.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker4_live_judge_dataurl_20260504T113455Z.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker4_openai_oauth_probe_20260504T113455Z.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker4_openai_oauth_https_probe_20260504T113455Z.log`
- `poc/tasks/native_chart_style_deck/evidence/worker4_live_judge_dataurl_20260504T113455Z.log`
- `poc/tasks/native_chart_style_deck/evidence/worker4_openai_oauth_probe_20260504T113455Z.log`
- `poc/tasks/native_chart_style_deck/evidence/worker4_openai_oauth_https_probe_20260504T113455Z.log`

Live judge run outcomes:

| Package | Command outcome | Score |
|---|---:|---:|
| `annotated_layout_repair_deck` | exit `0` | `57.00/57.00` |
| `public_template_compliance_deck` | exit `0` | `58.00/58.00` |
| `native_chart_style_deck` | exit `0` | `71.00/71.00` |

## `codex-exec` baseline evidence

Baseline command shape:

```bash
timeout 140s uv run cuif-eval run-and-evaluate \
  --task poc/tasks/<task_id> \
  --bundle output/bundles/worker4_task6/<task_id>_codex_20260504T113455Z \
  --run output/runs/worker4_task6/<task_id>_codex_20260504T113455Z \
  --agent codex-exec \
  --agent-arg=--model --agent-arg=gpt-5.3-codex-spark \
  --overwrite-bundle \
  --skip-judges
```

Package-local logs:

- `poc/tasks/annotated_layout_repair_deck/evidence/worker4_codex_baseline_20260504T113455Z.log`
- `poc/tasks/public_template_compliance_deck/evidence/worker4_codex_baseline_20260504T113455Z.log`
- `poc/tasks/native_chart_style_deck/evidence/worker4_codex_baseline_20260504T113455Z.log`

Baseline outcomes:

| Package | Outcome | Score / follow-up |
|---|---|---:|
| `annotated_layout_repair_deck` | `run-and-evaluate` exit `0` | `57.00/57.00` |
| `public_template_compliance_deck` | outer timeout `124` after both codex turns completed | follow-up `evaluate-bundle` exit `0`, `18.00/58.00` |
| `native_chart_style_deck` | `run-and-evaluate` exit `0` | `60.00/71.00` |

## Verification

- `uv run python -m compileall -q src tests` -> exit `0`
- `uv run cuif-eval validate poc/tasks/annotated_layout_repair_deck/manifest.yaml --skip-judges` -> exit `0`
- `uv run cuif-eval validate poc/tasks/public_template_compliance_deck/manifest.yaml --skip-judges` -> exit `0`
- `uv run cuif-eval validate poc/tasks/native_chart_style_deck/manifest.yaml --skip-judges` -> exit `0`
- `uv run pytest -q` -> `54 passed in 4.01s`
- `git diff --check` -> exit `0`
