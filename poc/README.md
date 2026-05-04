# CUIF PoC task packages

This directory contains proof-of-concept task packages for the CUIF office-family evaluation pipeline. The toy task is intentionally smoke-test quality: it exercises the full author/evaluator boundary without pretending to be a benchmark-quality example.

For manually authoring the next 2--3 PoC tasks, follow the detailed [task generation guide](task-generation-guide.md).

## Task layout

A task package is a directory with `manifest.yaml`, immutable package artifacts under `artifacts/`, and optional deterministic mock outputs under `mock_outputs/`.

Key namespaces:

- `package.<name>`: immutable author-supplied artifacts such as seeds, sketches, and gold files.
- `run.outputs.<turn>.<name>`: adapter-produced artifacts under a run workspace.
- `previews/`, `report.json`, `report.md`, and `review/index.html`: evaluator-generated outputs, never authored package artifacts.

## Deterministic smoke run

```bash
uv run cuif-eval validate poc/tasks/toy_pptx_layout/manifest.yaml
uv run cuif-eval run --task poc/tasks/toy_pptx_layout --adapter mock --out output/runs/toy_pptx_layout_mock --skip-judges
```

The mock adapter copies `mock_outputs/<turn>/result.pptx` into the isolated run workspace, then the evaluator runs deterministic PPTX checks, optional renderer fallback, skipped judge diagnostics, and static report generation.

For layout-constraint task review, summarize scoring allocation before
acceptance:

```bash
uv run cuif-eval point-distribution poc/tasks/<task_id>/manifest.yaml --fail-below-threshold
```

See [layout-heavy evaluator verification templates](evaluator-verification-templates.md)
for point-distribution, live `gpt-5.4` judge, and Codex baseline evidence commands.

## Adapter contracts

- `mock`: copies deterministic fixture outputs for CI and local smoke tests.
- `command`: prepares per-turn instruction files and documented environment variables (`CUIF_TASK_DIR`, `CUIF_WORK_DIR`, `CUIF_OUTPUT_DIR`, `CUIF_TURN_ID`, `CUIF_INSTRUCTION_FILE`) for future GUI/open-tool agents. `CUIF_TASK_DIR` points at the copied run-local `task/` directory, not the source package. Pass `--command '<template>'` to execute a command; omit it to prepare the workspace only.
- `manual`: writes instructions for a human or pure-GUI workflow without claiming evaluation completed.

## Optional live LLM/VLM judges

Default verification uses `--skip-judges` and performs no network calls. For an OpenAI-compatible local endpoint, launch:

```bash
npx openai-oauth
uv run cuif-eval run --task poc/tasks/toy_pptx_layout --adapter mock --out output/runs/toy_pptx_layout_judge --judge-base-url http://127.0.0.1:<port>/v1 --judge-model <model>
```

Judge responses are cached in the run workspace under `judge_cache/` using a key that includes model, endpoint, prompt/rubric, artifact references, artifact digests, rendered image paths, and rendered image digests.

`llm_text_rubric` sends a text-only `/chat/completions` request with a structured PPTX text/layout summary. `vlm_layout_rubric` first renders the target PPTX to PNG preview assets with LibreOffice/`soffice`; when at least one PNG is produced, it sends those PNGs as `image_url` content blocks to the same OpenAI-compatible endpoint. If rendering is unavailable, optional VLM checks are skipped and required VLM checks are blocked with renderer evidence.

Most OpenAI-compatible servers accept base64 `data:` image URLs. `openai-oauth` 1.0.2 requires `http`/`https` image URLs, so expose the run directory through a public/static file URL when doing a true live VLM pass and pass the run-local URL root:

```bash
uv run cuif-eval run \
  --task poc/tasks/toy_pptx_layout \
  --adapter mock \
  --out output/runs/toy_pptx_layout_judge \
  --judge-base-url http://127.0.0.1:<port>/v1 \
  --judge-model <model> \
  --judge-image-url-base https://<public-host>/toy_pptx_layout_judge
```

## Evidence organization

Task packages live under `poc/tasks/<task_id>/` and should contain only
package-authored materials: `manifest.yaml`, `artifacts/`, `mock_outputs/`,
task cards/README files, and reproducible generation scripts. Runtime evidence
from Ralph/team runs, live judge attempts, Codex baselines, rendered previews,
and other logs should stay in ignored runtime locations such as `output/` or
`.omx/`, not inside task package directories.
