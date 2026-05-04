# Layout-heavy evaluator verification templates

Use these commands when reviewing the new layout-constraint PPTX task packages. Replace
`<task_id>` with the package directory name under `poc/tasks/`.

## Point distribution review

The thesis-heavy percentage excludes boilerplate `file_exists`, `pptx_slide_count`,
and diagnostic preview-only checks such as `rendered_layout_review`.

```bash
uv run cuif-eval point-distribution poc/tasks/<task_id>/manifest.yaml --json
uv run cuif-eval point-distribution poc/tasks/<task_id>/manifest.yaml --fail-below-threshold
```

Review fields:

- `thesis_heavy_points / review_points` should normally be at least `60%`.
- Thesis-heavy buckets are `layout_template_style`, `native_editability`, and
  `preservation_regression`.
- `diagnostic` and `boilerplate` buckets do not count in the denominator.

## Live judge attempt template

Default deterministic validation should use `--skip-judges`. For live VLM/LLM
evidence, run `openai-oauth` when available and target `gpt-5.4`:

```bash
npx openai-oauth
uv run cuif-eval run \
  --task poc/tasks/<task_id> \
  --adapter mock \
  --out output/runs/<task_id>_judge \
  --judge-base-url http://127.0.0.1:<port>/v1 \
  --judge-model gpt-5.4 \
  --refresh-judge-cache
```

If `vlm_layout_rubric` needs HTTP(S) image URLs with `openai-oauth`, expose the
run directory and include:

```bash
  --judge-image-url-base https://<public-host>/<task_id>_judge
```

Evidence to record:

- command used;
- run directory;
- live endpoint/model;
- pass/fail/error status for judge checks;
- blocker text when credentials, endpoint, or image hosting are unavailable.

## Codex baseline attempt template

Run or document this baseline attempt before final acceptance:

```bash
uv run cuif-eval run-and-evaluate \
  --task poc/tasks/<task_id> \
  --bundle output/bundles/<task_id> \
  --run output/runs/<task_id>_codex \
  --agent codex \
  --overwrite-bundle \
  --skip-judges
```

Evidence to record:

- bundle path;
- run path;
- agent logs path;
- final score and report path;
- any command/credential/tooling failure.

## Evaluator adequacy report template

| Task | Thesis claim | Evaluator(s) | Point share | Blind spot | Owner | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `<task_id>` | Layout/template/style/preservation/native claim | `pptx_bbox_region`, `pptx_style_check`, `pptx_chart_data`, `pptx_preservation_diff`, `vlm_layout_rubric` as applicable | `<share>` | `<known limitation>` | `<worker>` | pass/fix/block |

Notes:

- `pptx_style_check` supports text run style (`font_color`, `font_size_pt`,
  `bold`) and shape-level template colors (`fill_color`, `line_color`).
- Use `pptx_chart_data` plus `pptx_bbox_region` for native editable chart data
  and chart placement.
- Use `rendered_layout_review` as preview evidence only; pair it with a scoring
  check when layout correctness must affect the grade.
