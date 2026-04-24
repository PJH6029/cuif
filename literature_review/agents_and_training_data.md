# Office-task agents and training data

This file summarizes agents that are directly relevant to office-family computer-use tasks, then lists training/data resources that can support a CUIF-style benchmark or future office-task agent.

## Relevant office-task agents

| Agent/system | Office scope | Evaluated on | Core method | Notes for CUIF |
|---|---|---|---|---|
| [SheetCopilot](https://github.com/BraveGroup/SheetCopilot) | Excel | SheetCopilot benchmark | LLM plans/executes spreadsheet actions through a predefined operation/action space; feedback loop over Excel/Google Sheets | Good example of spreadsheet action taxonomy and Windows Excel harness |
| [ROGA](https://github.com/morgen52/roga) | Excel/Word/PPT file objects; audited eval on SheetCopilot | SheetCopilot | Planner chooses `toolgen`, `toolexec`, `codeexec`, `done`; dynamically generates task-specific tools, validates them in a shadow sandbox, executes on office file objects | Strong office-agent pattern: generate specialized tools instead of only primitive GUI actions |
| [PPTPilot](https://github.com/michaelofengend/PPTArena) | PowerPoint editing | PPTArena/PPTArena-like tasks | Structure-aware slide editing: semantic edit plans, routing between high-level programmatic edits and deterministic XML operations, iterative plan-edit-check verification | Strong candidate baseline for CUIF PPTX tasks; needs adaptation to multi-turn and cross-file tasks |
| [PPTAgent / DeepPresenter](https://github.com/icip-cas/PPTAgent) | PowerPoint generation | PPTEval / internal tasksets | Research/content extraction, asset creation, layout/code generation, VLM/LLM quality checks; DeepPresenter fine-tuning release noted in repo | Useful for generation-heavy PPT tasks, but not enough for precise editing/follow-up constraints |
| OfficeBench/OdysseyBench baseline agents | Word/Excel/PDF/email/calendar | OfficeBench/OdysseyBench | Prompted tool agents with app switching, memory/RAG variants for OdysseyBench | Useful cross-app orchestration baselines; weak artifact editing precision |
| OSWorld/WAA agents (e.g., screenshot+OCR/grounding agents, Navi/OmniParser-style systems) | Real desktop apps including office | OSWorld, WindowsAgentArena | Multimodal GUI control from screenshots/accessibility observations; action grounding in desktop | Useful as general computer-use baselines for CUIF when tasks run in real Office/LibreOffice GUI |

## SheetCopilot agent

**Primary source:** [SheetCopilot GitHub](https://github.com/BraveGroup/SheetCopilot), [arXiv](http://arxiv.org/abs/2305.19308).  
**Audited clone:** `/tmp/cuif_lit_repos/SheetCopilot` at `c250f59`.

SheetCopilot is both a benchmark and an agent. The benchmark defines an action space of 44 spreadsheet operations. The agent uses an LLM to plan and execute actions against Excel/Google Sheets, with execution feedback. The evaluation harness reports:

- `Exec@1`: whether execution produced a valid output workbook/log;
- `Pass@1`: whether the output workbook matches reference solutions through check boards;
- category-level pass rates;
- action cost statistics.

**CUIF lesson:** expose a clear operation taxonomy for office artifacts, but do not restrict all agents to that taxonomy. CUIF can support GUI agents, code agents, XML/file agents, and hybrid agents while grading outputs/trajectories through a common rubric.

## ROGA

**Primary source:** [ROGA GitHub](https://github.com/morgen52/roga).  
**Audited clone:** `/tmp/cuif_lit_repos/ROGA` at `0f007cc`.

ROGA is a newer office-task agent scaffold for Windows artifacts. It is evaluated in the repo on SheetCopilot.

### Architecture

Audited code paths:

- `roga/core/session.py`
- `roga/core/tool_creator.py`
- `roga/prompt/planner.py`
- `roga/eval_sheetcopilot.py`

The planner alternates JSON actions:

- `toolgen`: generate a reusable task-specific office tool;
- `toolexec`: execute a generated tool;
- `codeexec`: execute code directly;
- `done`: terminate.

The sandbox loads Excel/Word/PPT into file objects (`openpyxl`, `docx`, `pptx` style abstractions), maintains unified memory/code context, validates generated tools in a shadow sandbox, executes them, and can revise failed tools while preserving tool IDs. Output artifacts are saved as `new_object.xlsx`, `new_object.pptx`, etc.

### Evaluation

`eval_sheetcopilot.py` uses SheetCopilot-style metrics:

- Exec@1 if logs indicate finish and output exists;
- output rate if `new_object.xlsx` exists;
- Pass@1 if output matches any SheetCopilot reference through check boards.

**CUIF lesson:** ROGA is a strong baseline idea for office tasks that need artifact manipulation beyond primitive clicks. A CUIF benchmark should not force only GUI interaction; it should compare GUI, file/XML, code, and hybrid office agents under the same task requirements.

## PPTPilot / PPTArena agent

**Primary source:** [PPTArena GitHub](https://github.com/michaelofengend/PPTArena), [arXiv](https://arxiv.org/abs/2512.03042).  
**Audited clone:** `/tmp/cuif_lit_repos/PPTArena_michael` at `b5a5d59`.

The paper/repo pair introduces PPTPilot, described as a structure-aware PowerPoint editing agent. Its key ideas are directly aligned with CUIF PPTX work:

- plan semantic edit sequences rather than one-shot file mutation;
- route between high-level programmatic tools and deterministic XML operations;
- preserve visual fidelity through iterative plan-edit-check;
- use structure and rendered visual checks.

The benchmark evaluator separately scores instruction following and visual quality. This can be used both as an evaluation method and as an agent self-checking loop.

**CUIF lesson:** for practical PowerPoint tasks, a strong agent likely needs access to both semantic object-level operations and low-level OOXML precision. GUI-only agents may struggle with exact layout/style; XML-only agents may struggle with visual judgment and feature coverage.

## PPTAgent / DeepPresenter

**Primary source:** [PPTAgent GitHub](https://github.com/icip-cas/PPTAgent), [PPTAgent arXiv](https://arxiv.org/abs/2501.03936).  
**Audited clone:** `/tmp/cuif_lit_repos/PPTAgent` at `5327bbc`.

PPTAgent targets presentation generation more than editing. Its evaluation (`pptagent/ppteval.py`) renders slides and uses VLM/LLM scoring for:

- vision/style;
- content;
- logical coherence.

The README also describes DeepPresenter releases, including fine-tuned models/tasksets. These are useful for generation-heavy tasks and for studying slide-generation data scaling.

**CUIF lesson:** generation-quality metrics are necessary but insufficient. CUIF tasks should combine quality metrics with instruction-specific constraints and preservation/collateral-damage checks.

## OfficeBench and OdysseyBench agents

**Primary sources:** [OfficeBench](https://github.com/zlwang-cs/OfficeBench), [OdysseyBench](https://github.com/microsoft/OdysseyBench).  
**Audited clones:** OfficeBench `b978b80`, OdysseyBench `3389881`.

These benchmarks include app/tool-based agents for cross-application workflows. OdysseyBench adds memory/RAG configurations for long chat histories:

- raw chat context;
- RAG over dialogue sessions/utterances;
- RAG over summary sessions/chunks;
- top-k retrieval.

HomerAgents is a benchmark/data generation framework that synthesizes long-horizon office workflows through environment exploration, task generation, and dialogue synthesis.

**CUIF lesson:** if CUIF includes multi-turn or long-horizon user histories, memory retrieval should be a baseline axis. But CUIF should also add artifact-level grading much richer than OfficeBench/OdysseyBench.

## General computer-use agents as CUIF baselines

CUIF should also evaluate general GUI agents because practical office tasks often run in real apps:

- OSWorld agents: screenshot/accessibility-driven agents operating desktop VMs ([OSWorld](https://github.com/xlang-ai/OSWorld));
- WindowsAgentArena agents: Windows desktop control at scale, e.g., Navi/OmniParser-style perception/action stacks ([WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena));
- AndroidWorld-style agents are less office-specific but useful for dynamic task generation and durable reward design ([AndroidWorld](https://github.com/google-research/android_world)).

These agents are important negative/contrast baselines: they can use the real UI, but may be inefficient or imprecise on Office XML/layout operations.

## Training and scalable data resources

| Dataset/resource | Size/scope | Supervision | How data is generated/collected | Use for CUIF |
|---|---:|---|---|---|
| [InstructExcel](https://github.com/microsoft/InstructExcel) | 10,520 NL-to-OfficeScripts examples | Instruction -> code | Collected/constructed Excel instruction-code pairs with train/dev/test splits | Fine-tune/retrieve Excel scripting actions; not sufficient for state eval |
| [SheetCopilot](https://github.com/BraveGroup/SheetCopilot) | 221 tasks, 28 workbooks, 67 seed tasks, 44 operations | Task -> action/reference workbook/check board | Human/seed tasks expanded into benchmark with reference outputs | Excel operation taxonomy and check-board examples |
| [SpreadsheetBench](https://github.com/RUCKBReasoning/SpreadsheetBench) | 912 tasks, 2,729 tests | Instruction + input workbook -> expected answer cells/ranges | Real-world forum questions with multiple test cases | Hidden-test-style formula/value eval; train/test examples for spreadsheet coding agents |
| [PPTC](https://github.com/gydpku/PPTC) | 279 sessions, 1,808 turns in audited data | Per-turn instruction -> feasible API sequence -> label PPT | PPT API scripts produce intermediate labels | Multi-turn PPT API imitation and per-turn artifact supervision |
| [PPTC-R](https://github.com/ZekaiGalaxy/PPTCR) | PPTC-derived robust variants | Perturbed instruction -> same/modified target | Paraphrase/noisy/multilingual/API perturbations | Robustness augmentation ideas |
| [OdysseyBench](https://github.com/microsoft/OdysseyBench) | 300 plus + 302 neo tasks in audited clone | Long chat histories + final task + rule eval | HomerAgents generates/synthesizes long-horizon office workflows and dialogues | Multi-turn/context generation template for office workflows |
| [PPTAgent/DeepPresenter](https://github.com/icip-cas/PPTAgent) | Repo states released fine-tuned models/taskset | Prompt/documents/assets -> generated deck | Presentation generation pipeline and fine-tuning releases | Style/content/coherence data for deck generation |
| [Mind2Web](https://github.com/OSU-NLP-Group/Mind2Web) / [Multimodal-Mind2Web](https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web) | >2,000 web tasks with action traces; screenshots in multimodal variant | Step-level action traces | Crowdsourced web task trajectories over live websites | Trajectory imitation and step-level metrics design; not office artifacts |
| [AppWorld](https://github.com/stonybrooknlp/appworld) | 9 apps, 457 APIs; task sets with tests | API/code agent tasks with hidden unit tests | Simulated app world and database state tests | Unit-test partial scoring pattern for office artifact requirements |
| [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) | 175 professional tasks | Checkpoint-weighted evaluators, sometimes trajectory-aware | Human-written workplace tasks over self-hosted apps | Best template for practical checkpoint partial credit incl. office-like files |
| [tau2/tau3-bench](https://github.com/sierra-research/tau2-bench) | Customer-service domains, text/voice/knowledge | Multi-turn task policies, action/env/communication reward components | Simulated user-agent-tool interactions | Multi-turn interaction/evaluator component model; not office-specific |
| [AndroidWorld](https://github.com/google-research/android_world) | 116 Android tasks, parameterized into many variants | Durable reward validators | Hand-crafted tasks with random parameters | Dynamic task instantiation and robust validators |

## Gaps in training data

The literature has pieces of the desired CUIF data, but not the whole object:

- There is **no large open dataset** of multi-turn, multimodal, practical PPTX/DOCX/XLSX editing trajectories with per-turn partial-credit labels.
- PPTC has multi-turn PPT data, but it is API-primitive and text-only.
- InstructExcel and SpreadsheetBench support Excel code/value tasks, but not rich office workflows or multimodal layout constraints.
- SheetCopilot has rich Excel operations/checks, but only 221 tasks and final pass/fail.
- OdysseyBench scales long-horizon office workflows and dialogue histories, but it excludes PPTX and still uses shallow final checks.
- PPTArena improves PowerPoint evaluation but remains mostly single-shot final-file judging.

## Recommendations for scalable CUIF data generation

1. **Start with executable task programs.** Generate gold artifacts and intermediate states by executing deterministic office scripts/OOXML transformations, then convert them into natural-language and multimodal instructions.
2. **Use templates plus perturbations.** For each seed workflow, vary source data, visual style, user-turn order, constraints, and distractors. This follows SpreadsheetBench hidden tests and AndroidWorld parameterization.
3. **Generate visual constraints from artifacts.** Render decks/docs/sheets, then create sketch-like images or annotation overlays from bounding boxes; use these as multimodal instructions.
4. **Keep evaluator leaves executable.** Every generated requirement should map to a known evaluator leaf where possible: cell check, shape check, rendered visual region, VLM rubric, etc.
5. **Add human or LLM review only after deterministic checks.** Use VLM/LLM judges for aesthetics/semantics, but keep deterministic checks for concrete constraints.
6. **Record per-turn gold states.** If a task has multiple user turns, save expected or acceptable artifact states after each turn so trajectory/per-turn scoring is possible.
7. **Support multiple solution paths.** Store rubrics and invariants rather than one exact file whenever task has many valid solutions; accept reference sets for deterministic tasks.
8. **Use generated data for training cautiously.** Separate public train/dev tasks from hidden evaluation families; avoid train/test leakage through templates and artifacts.

## Candidate baselines for a CUIF paper

For a paper, compare across at least these families:

- **General GUI agents:** OSWorld/WAA-style screenshot agents, OpenAI/Anthropic/Gemini computer-use tools if available, UI-TARS/OmniParser-like open agents where runnable.
- **Office artifact agents:** ROGA, PPTPilot, SheetCopilot-like Excel agent, code/OOXML agents based on python-pptx/openpyxl/python-docx.
- **LLM code agents:** a ReAct/code-execution baseline that directly scripts `python-pptx`, `openpyxl`, and `python-docx`.
- **Ablations:** no visual input, no per-turn memory, no self-check, GUI-only vs file-only vs hybrid.

Report not only overall success but also:

- PPTX/DOCX/XLSX family score;
- multimodal instruction adherence;
- per-turn score;
- final artifact score;
- collateral-damage penalty;
- trajectory efficiency/action cost;
- model/tool cost.
