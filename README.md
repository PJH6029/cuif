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
- Optional OpenAI-compatible LLM/VLM judge checks with skip/cache behavior. VLM checks render PPTX artifacts to PNG previews and send those images through `/chat/completions` image content when live judges are enabled; `--judge-image-url-base` supports `openai-oauth` deployments that require HTTP(S) image URLs.

See `poc/README.md` for task authoring and adapter details.

## External-agent bundle flow

For agents that run outside this evaluator process, such as Codex App with Computer Use, export a task-facing bundle, let the agent write turn outputs, then import/evaluate those outputs:

```bash
uv run cuif-eval export-bundle \
  --task poc/tasks/transformer_paper_review_deck \
  --out ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck \
  --overwrite

# Open only .../transformer_paper_review_deck/current in the evaluated agent.
# The first turn is staged in current/instruction.md with only turn1 inputs visible.

uv run cuif-eval stage-bundle-turn \
  --bundle ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck \
  --turn turn2

uv run cuif-eval stage-bundle-turn \
  --bundle ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck \
  --turn final

# The agent writes outputs/turn1/result.pptx, outputs/turn2/result.pptx, and outputs/final/result.pptx as turns are staged.

uv run cuif-eval evaluate-bundle \
  --task poc/tasks/transformer_paper_review_deck \
  --workspace ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck/current \
  --run output/codex_computer_use_runs/transformer_paper_review_deck \
  --skip-judges
```

The bundle keeps operator files under `.cuif_bundle/` and stages only the first turn in `current/instruction.md`. Use `stage-bundle-turn` when you are ready to reveal a later turn; it updates `current/instruction.md` and copies only that turn's newly declared textual/visual inputs into `current/inputs/<turn>/`.

To run an already exported bundle through an agent runner, use `run-agent`. This handles turn execution and staging, but leaves evaluation as a separate step:

```bash
uv run cuif-eval run-agent \
  --bundle ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck \
  --agent codex-exec

uv run cuif-eval evaluate-bundle \
  --task poc/tasks/transformer_paper_review_deck \
  --workspace ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck/current \
  --run output/codex_exec_runs/transformer_paper_review_deck \
  --skip-judges
```

For a single wrapper command that exports, runs the selected agent, and evaluates:

```bash
uv run cuif-eval run-and-evaluate \
  --task poc/tasks/transformer_paper_review_deck \
  --bundle ~/code/snupi/cuif-agents-evaluation/transformer_paper_review_deck \
  --run output/codex_exec_runs/transformer_paper_review_deck \
  --agent codex-exec \
  --overwrite-bundle \
  --skip-judges
```

The initial agent runner is `codex-exec`, which runs `codex exec --cd <bundle>/current --json --yolo --skip-git-repo-check` once per turn. Additional flags can be passed with repeated `--agent-arg` values.
