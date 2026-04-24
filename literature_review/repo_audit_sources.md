# Repository audit notes and source index

This review combines web/paper search with code inspection. Repositories were cloned outside this project under `/tmp/cuif_lit_repos` so the CUIF repo stays small.

## Audited repositories

| Repo | Local clone | Commit | Important audited paths |
|---|---|---:|---|
| [OfficeBench](https://github.com/zlwang-cs/OfficeBench) | `/tmp/cuif_lit_repos/OfficeBench` | `b978b80` | `evaluation.py`, `utils/evaluate.py`, `tasks/*/subtasks/*.json` |
| [SpreadsheetBench](https://github.com/RUCKBReasoning/SpreadsheetBench) | `/tmp/cuif_lit_repos/SpreadsheetBench` | `49b73a9` | `evaluation/evaluation.py`, `evaluation/open_spreadsheet.py`, dataset metadata |
| [SheetCopilot](https://github.com/BraveGroup/SheetCopilot) | `/tmp/cuif_lit_repos/SheetCopilot` | `c250f59` | `agent/evaluation.py`, `agent/utils/eval.py`, check YAMLs |
| [PPTC](https://github.com/gydpku/PPTC) | `/tmp/cuif_lit_repos/PPTC` | `277f56f` | `src/evaluate.py`, `src/pptx_check.py`, data JSONs |
| [PPTC-R](https://github.com/ZekaiGalaxy/PPTCR) | `/tmp/cuif_lit_repos/PPTCR` | `080f0cc` | README, `src/evaluate.py`, language/robust/noisy scripts |
| [PPTAgent](https://github.com/icip-cas/PPTAgent) | `/tmp/cuif_lit_repos/PPTAgent` | `5327bbc` | README, `pptagent/ppteval.py` |
| [PPTArena / PPTPilot](https://github.com/michaelofengend/PPTArena) | `/tmp/cuif_lit_repos/PPTArena_michael` | `b5a5d59` | `run_evaluation.py`, `src/llm/judge.py`, `src/evaluation_pairs_refined.json` |
| [OdysseyBench](https://github.com/microsoft/OdysseyBench) | `/tmp/cuif_lit_repos/OdysseyBench` | `3389881` | `evaluation/main.py`, `evaluation/task_evaluator.py`, `utils/evaluate.py`, `llm-as-a-judge.py`, `tasks/*/subtasks_*/*.json` |
| [OSWorld](https://github.com/xlang-ai/OSWorld) | `/tmp/cuif_lit_repos/OSWorld` | `c7e54d2` | `desktop_env/desktop_env.py`, `desktop_env/evaluators/metrics/slides.py`, `table.py`, `docs.py`, task examples |
| [WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena) | `/tmp/cuif_lit_repos/WindowsAgentArena` | `6d39ed8` | README, `docs/Develop-Tasks.md`, run/eval scripts |
| [WorkArena](https://github.com/ServiceNow/WorkArena) | `/tmp/cuif_lit_repos/WorkArena` | `a772230` | README, task validation tests/demos |
| [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) | `/tmp/cuif_lit_repos/TheAgentCompany` | `98b68ef` | `workspaces/base_image/scoring.py`, task evaluators for spreadsheet/slides/docs |
| [InstructExcel](https://github.com/microsoft/InstructExcel) | `/tmp/cuif_lit_repos/InstructExcel` | `0cea28a` | `instruct_excel_benchmark.json`, `experiment_code/run_few_shot.py`, construction scripts |
| [ROGA](https://github.com/morgen52/roga) | `/tmp/cuif_lit_repos/ROGA` | `0f007cc` | `roga/core/session.py`, `roga/core/tool_creator.py`, `roga/prompt/planner.py`, `roga/eval_sheetcopilot.py` |
| [Mind2Web](https://github.com/OSU-NLP-Group/Mind2Web) | `/tmp/cuif_lit_repos/Mind2Web` | `33bd95c` | `src/action_prediction/metric.py`, README/data description |
| [VisualWebArena](https://github.com/web-arena-x/visualwebarena) | `/tmp/cuif_lit_repos/VisualWebArena` | `89f5af2` | `evaluation_harness/evaluators.py` |
| [WebArena](https://github.com/web-arena-x/webarena) | `/tmp/cuif_lit_repos/WebArena` | `dce0468` | README/evaluation harness for comparison |
| [AppWorld](https://github.com/stonybrooknlp/appworld) | `/tmp/cuif_lit_repos/AppWorld` | `a072b7a` | `src/appworld/evaluator.py`, README |
| [tau-bench](https://github.com/sierra-research/tau-bench) | `/tmp/cuif_lit_repos/tau_bench` | `59a200c` | `tau_bench/envs/base.py`, `tau_bench/run.py` |
| [tau2/tau3-bench](https://github.com/sierra-research/tau2-bench) | `/tmp/cuif_lit_repos/tau2_bench` | `ada8e51` | `src/tau2/evaluator/*`, `src/tau2/metrics/agent_metrics.py`, `src/tau2/orchestrator/README.md` |
| [AndroidWorld](https://github.com/google-research/android_world) | `/tmp/cuif_lit_repos/AndroidWorld` | `d9c569f` | README, `android_world/task_evals/*`, common validators |

## Paper/project links

### Office-family benchmarks and agents

- OfficeBench: [GitHub](https://github.com/zlwang-cs/OfficeBench), [arXiv 2407.19056](https://arxiv.org/abs/2407.19056), [project page](https://lzylucy.github.io/officebench/).
- OdysseyBench: [GitHub](https://github.com/microsoft/OdysseyBench), [arXiv 2508.09124](https://arxiv.org/abs/2508.09124), [OpenReview](https://openreview.net/forum?id=tMbmBCfSTz).
- SpreadsheetBench: [GitHub](https://github.com/RUCKBReasoning/SpreadsheetBench), [arXiv 2406.14991](https://arxiv.org/abs/2406.14991), [project page](https://spreadsheetbench.github.io/).
- SheetCopilot: [GitHub](https://github.com/BraveGroup/SheetCopilot), [arXiv 2305.19308](http://arxiv.org/abs/2305.19308), [OpenReview](https://openreview.net/forum?id=tfyr2zRVoK).
- InstructExcel: [GitHub](https://github.com/microsoft/InstructExcel), [arXiv 2310.14495](https://arxiv.org/abs/2310.14495).
- PPTC: [GitHub](https://github.com/gydpku/PPTC), [arXiv 2311.01767](https://arxiv.org/abs/2311.01767).
- PPTC-R: [GitHub](https://github.com/ZekaiGalaxy/PPTCR).
- PPTAgent / DeepPresenter: [GitHub](https://github.com/icip-cas/PPTAgent), [PPTAgent arXiv 2501.03936](https://arxiv.org/abs/2501.03936).
- PPTArena / PPTPilot by Ofengenden et al.: [GitHub](https://github.com/michaelofengend/PPTArena), [arXiv 2512.03042](https://arxiv.org/abs/2512.03042), [Hugging Face paper page](https://huggingface.co/papers/2512.03042).
- PPTArena by Gandhi et al. (ICLR 2026 submission): [OpenReview](https://openreview.net/forum?id=Dl1S4EvFwh).
- ROGA: [GitHub](https://github.com/morgen52/roga).

### Computer-use / agent benchmarks for evaluation patterns

- OSWorld: [GitHub](https://github.com/xlang-ai/OSWorld), [arXiv 2404.07972](https://arxiv.org/abs/2404.07972), [project page](https://os-world.github.io/).
- WindowsAgentArena: [GitHub](https://github.com/microsoft/WindowsAgentArena), [arXiv 2409.08264](https://arxiv.org/abs/2409.08264), [OpenReview](https://openreview.net/forum?id=W9s817KqYf).
- TheAgentCompany: [GitHub](https://github.com/TheAgentCompany/TheAgentCompany), [arXiv 2412.14161](https://arxiv.org/abs/2412.14161).
- WorkArena: [GitHub](https://github.com/ServiceNow/WorkArena), [arXiv 2403.07718](https://arxiv.org/abs/2403.07718).
- WorkArena++: [arXiv 2407.05291](https://arxiv.org/abs/2407.05291).
- Mind2Web: [GitHub](https://github.com/OSU-NLP-Group/Mind2Web), [arXiv 2306.06070](https://arxiv.org/abs/2306.06070), [Multimodal-Mind2Web HF](https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web).
- VisualWebArena: [GitHub](https://github.com/web-arena-x/visualwebarena), [arXiv 2401.13649](https://arxiv.org/abs/2401.13649).
- WebArena: [GitHub](https://github.com/web-arena-x/webarena).
- AppWorld: [GitHub](https://github.com/stonybrooknlp/appworld), [arXiv 2407.18901](https://arxiv.org/abs/2407.18901).
- tau-bench: [GitHub](https://github.com/sierra-research/tau-bench), [arXiv 2406.12045](https://arxiv.org/abs/2406.12045).
- tau2/tau3-bench: [GitHub](https://github.com/sierra-research/tau2-bench), current README references tau3 additions including voice, knowledge, and task fixes.
- AndroidWorld: [GitHub](https://github.com/google-research/android_world), [paper PDF](https://arxiv.org/pdf/2405.14573), [project page](https://google-research.github.io/android_world/).

## Quick code-level facts used in reports

### OfficeBench / OdysseyBench

- Eval item list is ANDed; any failed function returns task failure.
- Main task-completion functions: containment, file existence, exact match, Excel cell value/comparator, calendar overlap.
- OdysseyBench adds long chat histories and RAG configs but task success stays OfficeBench-like.

### SpreadsheetBench

- Recalculate workbook through LibreOffice/Excel before comparison.
- Load workbooks with `openpyxl(data_only=True)`.
- Compare only answer cells/ranges.
- Report soft fraction over test cases and hard all-test pass.

### SheetCopilot

- `Exec@1` requires a successful log/output file.
- `Pass@1` compares result workbook against any reference workbook through task-specific check boards.
- Rich checks include charts/pivots/filters/conditional formats, although some style paths are partially commented.

### PPTC/PPTC-R

- Multi-turn sessions have label PPT outputs per turn.
- Evaluation compares extracted text/style strings exactly and separately checks explicit spatial relation constraints.
- Turn and session modes exist, but each check is binary.

### PPTArena / PPTPilot

- `run_evaluation.py` converts decks to JSON, renders slide images, and calls a judge.
- `src/llm/judge.py` uses structural diffs for instruction following and rendered images for visual quality.
- Scores are 0--5 dimensions rather than binary success only.

### OSWorld / WindowsAgentArena

- Task configs specify evaluator functions, result getters, expected getters, and combination logic.
- Office metrics include detailed PPTX/XLSX/DOCX property comparisons.
- Evaluation is generally final-state.

### TheAgentCompany

- Evaluators return weighted checkpoints.
- Some office-like tasks combine deterministic checks with LLM/VLM checks.
- `trajectory_path` can be provided and is often used for partial-credit evidence.

### Mind2Web

- Step metrics: element accuracy, action F1, step accuracy.
- Reports both micro averages and macro averages per task/annotation.

### VisualWebArena

- Evaluator types include string, URL, programmatic HTML, and image query/VQA/SSIM.
- Component evaluator scores are multiplied.

### AppWorld

- Unit-test-like database checks produce pass percentages and all-pass success.
- Online evaluator can be queried during a run.

### tau2/tau3

- Reward can combine environment DB/assertion, action, communication, and NL assertion components.
- Full-duplex mode evaluates tick-grouped trajectories.
- Metrics include avg reward, pass^k, action stats, DB match, termination, and responsiveness.

## Not fully audited / caveats

- The ICLR 2026 PPTArena submission was reviewed from OpenReview/web snippets and paper text; no local code audit was performed.
- Some repos depend on Windows/Excel/PowerPoint or external APIs; code was inspected but not fully executed end-to-end.
- Leaderboard/SOTA rankings change rapidly. This review emphasizes benchmark/evaluator design and agent mechanisms rather than claiming stable numerical SOTA.
- OmniACT was searched as a multimodal desktop/web benchmark, but a reliable repo clone was not audited, so it is not used as a core source.
