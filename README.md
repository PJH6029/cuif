# CUIF PoC Evaluation Pipeline

This repository contains a proof-of-concept evaluation pipeline for practical office-family computer-use instruction following (CUIF). The current vertical slice is PPTX-first and intentionally ships a generated toy task so evaluator development can proceed before benchmark-quality handmade tasks exist.

## Quickstart

```bash
uv sync
uv run pytest
uv run cuif-eval validate poc/tasks/toy_pptx_layout/manifest.yaml
uv run cuif-eval run --task poc/tasks/toy_pptx_layout --adapter mock --out output/runs/toy_pptx_layout_mock --skip-judges
uv run cuif-eval report --run output/runs/toy_pptx_layout_mock
```

The smoke run creates:

- `outputs/turn1/result.pptx`
- `outputs/final/result.pptx`
- `report.json`
- `report.md`
- `review/index.html`

## What v0 covers

- Manifest-driven task packages with typed `package.*` and `run.outputs.*` artifact namespaces.
- Isolated run workspaces.
- Mock, command, and manual adapter contracts.
- Deterministic PPTX checks for file existence, slide count, text, normalized bbox regions, style, and preservation diffs.
- Dependency-aware partial-credit aggregation by check, turn, and final score.
- Optional rendered review fallback and static human review UI.
- Optional OpenAI-compatible judge checks with skip/cache behavior.

See `poc/README.md` for task authoring and adapter details.
