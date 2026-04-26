# CUIF PoC task packages

This directory contains proof-of-concept task packages for the CUIF office-family evaluation pipeline. The toy task is intentionally smoke-test quality: it exercises the full author/evaluator boundary without pretending to be a benchmark-quality example.

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

## Adapter contracts

- `mock`: copies deterministic fixture outputs for CI and local smoke tests.
- `command`: prepares per-turn instruction files and documented environment variables (`CUIF_TASK_DIR`, `CUIF_WORK_DIR`, `CUIF_OUTPUT_DIR`, `CUIF_TURN_ID`, `CUIF_INSTRUCTION_FILE`) for future GUI/open-tool agents. `CUIF_TASK_DIR` points at the copied run-local `task/` directory, not the source package. Pass `--command '<template>'` to execute a command; omit it to prepare the workspace only.
- `manual`: writes instructions for a human or pure-GUI workflow without claiming evaluation completed.

## Optional live judges

Default verification uses `--skip-judges` and performs no network calls. For an OpenAI-compatible local endpoint, launch:

```bash
npx openai-oauth
uv run cuif-eval run --task poc/tasks/toy_pptx_layout --adapter mock --out output/runs/toy_pptx_layout_judge --judge-base-url http://127.0.0.1:<port>/v1 --judge-model <model>
```

Judge responses are cached in the run workspace under `judge_cache/` using a key that includes model, endpoint, prompt/rubric, artifact references, and artifact digests.
