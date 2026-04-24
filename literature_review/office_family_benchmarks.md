# Office-family benchmark audit

This file focuses on office-family benchmarks and office-task subsets of broader computer-use benchmarks. Code paths refer to local clones under `/tmp/cuif_lit_repos` as audited on 2026-04-24.

## Summary matrix

| Benchmark | Office scope | Multiturn? | Multimodal task input? | Evaluation style | Partial credit? | Main gap for CUIF |
|---|---:|---:|---:|---|---:|---|
| [OfficeBench](https://github.com/zlwang-cs/OfficeBench) / [paper](https://arxiv.org/abs/2407.19056) | Word/Excel/PDF/email/calendar cross-app tasks; no PPTX | No user turns; multi-step agent workflow | Mostly text/files | Rule-based final state: file existence, keyword containment, exact match, Excel cells, calendar overlap | No | Practical cross-app tasks but shallow final checks and no PPTX/multimodal/per-turn score |
| [OdysseyBench](https://github.com/microsoft/OdysseyBench) / [paper](https://arxiv.org/abs/2508.09124) | Word/Excel/PDF/email/calendar long-horizon workflows | Uses long chat histories; task executed as final query | Mostly text histories/files | OfficeBench-style rule-based final state + LLM judge for data-generation quality | No for task success | Strong long-horizon/context story; evaluation still final and mostly keyword/value checks |
| [SpreadsheetBench](https://github.com/RUCKBReasoning/SpreadsheetBench) / [paper](https://arxiv.org/abs/2406.14991) | Excel from real forum questions | No | Text instructions + spreadsheets | Recalculate workbook, compare specified answer cells/ranges to gold across multiple tests | Soft pass fraction over tests; hard all-pass | Robust Excel value/formula generalization; weak on visual/layout/style and no trajectory |
| [SheetCopilot](https://github.com/BraveGroup/SheetCopilot) / [paper](https://arxiv.org/abs/2305.19308) | Excel operations incl. formatting/charts/pivots | No | Text + workbook | Excel COM/openpyxl check boards against reference workbooks | Exec@1/Pass@1 binary; cost stats | Rich Excel property checks but Windows/Excel-dependent and final-state only |
| [InstructExcel](https://github.com/microsoft/InstructExcel) / [paper](https://arxiv.org/abs/2310.14495) | NL-to-OfficeScripts for Excel | No | Text + spreadsheet context | Code string metrics: BLEU/ROUGE/exact/F1 and parameter-normalized variants | Token-level metrics, not artifact credit | Useful training data; not execution-based office artifact evaluation |
| [PPTC](https://github.com/gydpku/PPTC) / [paper](https://arxiv.org/abs/2311.01767) | PowerPoint creation/editing via API actions | Yes: per-turn instructions | Text only | Compare produced PPTX to turn/session labels; exact text/style plus explicit spatial relations | Separate string/position acc, but binary per turn/session | Multi-turn office benchmark exists, but tasks are primitive/API-like and text-only |
| [PPTC-R](https://github.com/ZekaiGalaxy/PPTCR) | Robust PPTC variants | Yes | Text; multilingual/noisy/robust instruction variants | Same as PPTC | Same as PPTC | Robustness extension, not richer office-task or multimodal eval |
| [PPTArena / PPTPilot](https://github.com/michaelofengend/PPTArena) / [arXiv](https://arxiv.org/abs/2512.03042) | PowerPoint in-place editing, 100 decks | Single instruction | Natural language + original/ground-truth PPTX; visual evaluation | Dual judge: structure JSON diff for instruction following + rendered-slide VLM visual quality, 0--5 scores | Yes, score dimensions but final-artifact only | Strong PPTX multimodal final judging; not multi-turn/per-turn trajectory |
| [PPTArena ICLR 2026 submission](https://openreview.net/forum?id=Dl1S4EvFwh) | PowerPoint Online tasks, 120 tasks across 12 files | Single task launch | GUI/VLM-compatible PowerPoint environment | Claimed tree-structured rubrics with programmatic/VLM/LLM checks and natural-language feedback | Yes, rubric partial credit | Very relevant; code not audited here; still final-file not action-sequence based per OpenReview snippet |
| [PPTAgent / DeepPresenter](https://github.com/icip-cas/PPTAgent) / [PPTAgent paper](https://arxiv.org/abs/2501.03936) | Presentation generation | Usually single prompt | Documents/assets/images possible | PPTEval: rendered slides + VLM/LLM score style/content/coherence 1--5 | Quality scores, not task subgoal credit | Presentation generation quality, not office instruction-following/edit benchmark |
| [OSWorld](https://github.com/xlang-ai/OSWorld) / [paper](https://arxiv.org/abs/2404.07972) | Real desktop; office subsets for LibreOffice/MS Office-like tasks | Agent trajectory multi-step; user instruction single-shot | Visual desktop observations | Task-specific final-state evaluator functions over files, UI, images | Sometimes averaged over multiple metrics; mostly binary | Broad realistic GUI but no multi-turn user tasking or rubric-rich office artifact partials |
| [WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena) / [paper](https://arxiv.org/abs/2409.08264) | Real Windows desktop incl. Office/browser tasks | Agent trajectory multi-step | Visual desktop observations | OSWorld-style task JSON evaluator functions and result aggregation | Mostly binary | Scalable Windows infra; office scoring inherited from task scripts |

## OfficeBench

**Primary source:** [GitHub](https://github.com/zlwang-cs/OfficeBench), [arXiv](https://arxiv.org/abs/2407.19056).  
**Audited clone:** `/tmp/cuif_lit_repos/OfficeBench` at `b978b80`.

### Scope and properties

OfficeBench contains 300 tasks. The task ID prefix encodes the number of applications: 93 one-app tasks, 95 two-app tasks, and 112 three-app tasks. It covers email, spreadsheets, text/Word/PDF documents, calendars, and cross-application workflows. It does **not** cover PowerPoint/PPTX.

From task configs, the evaluated document types and checks skew toward text containment and file creation:

- evaluator functions counted in task configs: `evaluate_contain` 279, `evaluate_file_exist` 233, `evaluate_excel_cell_value` 37, `evaluate_not_contain` 19, `evaluate_exact_match` 18, `evaluate_calendar_no_overlap` 6, `evaluate_diff_contain_text` 6, `evaluate_file_not_exist` 2, `evaluate_excel_cell_comparator` 1;
- doc types in eval configs: email 99, xlsx 57, txt 51, ics 47, docx 36, pdf 22, doc 10.

### Evaluation pipeline

Code paths:

- `evaluation.py`
- `utils/evaluate.py`

Pipeline:

1. For each task/subtask config, load a JSON `evaluation` list.
2. For each evaluation item, dispatch to a Python function named in the config.
3. **AND all checks**: if any item returns false, the subtask fails.
4. Aggregate binary pass rate by 1/2/3-app category and overall.

The check functions are deterministic and final-state-only:

- `evaluate_file_exist` / `evaluate_file_not_exist`: check paths under the task testbed.
- `evaluate_contain` / `evaluate_not_contain`: read text from xlsx/txt/ics/doc/docx/pdf/email and require keywords.
- `evaluate_diff_contain_text`: compare input/output textual diff and require keywords.
- `evaluate_excel_cell_value`: search a text dump for `(row, col): value`.
- `evaluate_excel_cell_comparator`: regex extract a cell text value and apply a comparator.
- `evaluate_exact_match`: compare file text/content exactly for selected types.
- `evaluate_calendar_no_overlap`: parse `.ics` and fail overlapping events.

### CUIF relevance

OfficeBench is useful for cross-app workflow inspiration and tool/app switching, but it is not enough for the proposed benchmark because it lacks PPTX, multimodal instructions, multi-turn user tasking, and nuanced layout/semantic/aesthetic scoring.

## OdysseyBench

**Primary source:** [GitHub](https://github.com/microsoft/OdysseyBench), [arXiv](https://arxiv.org/abs/2508.09124).  
**Audited clone:** `/tmp/cuif_lit_repos/OdysseyBench` at `3389881`.

OdysseyBench is the closest “long-horizon office workflow” benchmark found. It builds on OfficeBench and introduces two splits:

- OdysseyBench+ (`subtasks_plus`): 300 OfficeBench-derived tasks with dialogue histories;
- OdysseyBench-Neo (`subtasks_neo`): 302 newly synthesized tasks with chat histories.

The repo’s own task counts in the audited clone:

- plus: 300 tasks = 93 one-app, 95 two-app, 112 three-app;
- neo: 302 tasks = 60 one-app, 71 two-app, 171 three-app.

### Evaluation pipeline

Code paths:

- `evaluation/main.py`
- `evaluation/task_evaluator.py`
- `utils/evaluate.py`
- `llm-as-a-judge.py`

Task-completion evaluation is almost the same as OfficeBench:

1. Discover task/subtask JSON files.
2. Find the agent output folder under `tasks/{task_id}/outputs/{subtask_id}/{model}_{tag}/testbed`.
3. Load the task’s `evaluation` or `evaluation_criteria` list.
4. Dispatch the named `evaluate_*` functions and require all checks to pass.
5. Aggregate pass counts by app-count prefix and overall.

In the audited clone, task-completion eval functions included the OfficeBench checks plus a few Neo additions (`evaluate_keyword_exist`, `evaluate_doc_contain`, `evaluate_file_contains_keywords`, `evaluate_excel_sheet_exist`). The Neo split strongly increases DOCX/email-like keyword checks.

`llm-as-a-judge.py` is used for generation/data quality rather than task-completion scoring: it judges whether synthetic queries leak specific information and whether query+chat logs cover the original task description, using multiple LLM evaluations with majority/consensus.

### CUIF relevance

OdysseyBench is important because it directly attacks long-horizon context and synthetic office workflow generation (HomerAgents). However, its final success is still mostly keyword/file/cell based. It does not solve artifact-level PPTX/DOCX/XLSX visual fidelity, per-turn scoring, or multimodal instruction evaluation.

## SpreadsheetBench

**Primary source:** [GitHub](https://github.com/RUCKBReasoning/SpreadsheetBench), [arXiv](https://arxiv.org/abs/2406.14991), [project page](https://spreadsheetbench.github.io/).  
**Audited clone:** `/tmp/cuif_lit_repos/SpreadsheetBench` at `49b73a9`.

### Scope and properties

SpreadsheetBench contains 912 real-world Excel forum-style instructions and 2,729 test cases, about three tests per instruction. It focuses on cell-level and sheet-level manipulations. Each case specifies `answer_position` as cells/ranges to compare.

Evaluated properties are primarily final cell/range values after workbook recalculation. The repo contains style comparison helpers, but in the audited `evaluation/evaluation.py`, style comparison is commented out in the main cell comparison path.

### Evaluation pipeline

Code paths:

- `evaluation/open_spreadsheet.py`
- `evaluation/evaluation.py`

Pipeline:

1. Agent modifies an Excel workbook, usually by generating and executing Python code in a Docker/Jupyter environment.
2. `open_spreadsheet.py` opens/recalculates the workbook through LibreOffice or Excel COM so cached formula values are available to `openpyxl(data_only=True)`.
3. `compare_workbooks(gt_file, proc_file, instruction_type, answer_position)` loads both ground-truth and processed workbooks.
4. Only specified answer cells/ranges are compared.
5. `compare_cell_value` normalizes numeric values, datetimes, times, and empty/None cases.
6. Score is computed over multiple tests:
   - `soft_restriction`: fraction of test cases passed;
   - `hard_restriction`: 1 only if all test cases pass.

A repo caveat: at commit `49b73a9`, `proc_path` in `evaluation.py` points to an input path unless the output-path line is adjusted/uncommented or outputs overwrite inputs. Any benchmark reuse should fix this harness detail.

### CUIF relevance

SpreadsheetBench’s multi-test hidden-case structure is a strong pattern for formula/value generalization. It is weaker for style/layout, charts, rich spreadsheet UI properties, and trajectory or multi-turn evaluation.

## SheetCopilot

**Primary source:** [GitHub](https://github.com/BraveGroup/SheetCopilot), [OpenReview](https://openreview.net/forum?id=tfyr2zRVoK), [arXiv](http://arxiv.org/abs/2305.19308).  
**Audited clone:** `/tmp/cuif_lit_repos/SheetCopilot` at `c250f59`.

### Scope and properties

SheetCopilot has 221 tasks on 28 workbooks, derived from 67 seed tasks. It defines 44 spreadsheet operations across data entry/manipulation, workbook/sheet management, formatting, charts, and pivot tables.

Evaluated properties are richer than SpreadsheetBench:

- cell values;
- worksheets and structure;
- formatting/check-board entries;
- charts: type, title, legend, axes, series;
- pivot tables;
- filters;
- conditional formats.

Some cell-format comparison paths are partially commented in `agent/utils/eval.py`, so the precise property coverage depends on the task check YAMLs.

### Evaluation pipeline

Code paths:

- `agent/evaluation.py`
- `agent/utils/eval.py`

Pipeline:

1. For each task and repeated run, require an action log and result `.xlsx`.
2. Compute `Exec@1`: log has at least one success count and result file exists.
3. Compute `Pass@1`: compare result workbook with any reference solution under `dataset/task_sheet_answers_v2` using a task-specific YAML `*_check.yaml` check board.
4. Use Excel COM (`win32com.client`) to open workbooks and inspect charts/pivots/filters/formats where needed.
5. Report `Exec@1`, `Pass@1`, per-category execution/pass rates, and action cost statistics (`A_mean`, `A50_norm`, `A90_norm`).

### CUIF relevance

SheetCopilot is an important source for Excel property coverage and reference-solution matching. Its biggest limitations are Windows Excel dependency, final-state binary pass metrics, and lack of multi-turn/multimodal user instructions.

## InstructExcel

**Primary source:** [GitHub](https://github.com/microsoft/InstructExcel), [arXiv](https://arxiv.org/abs/2310.14495).  
**Audited clone:** `/tmp/cuif_lit_repos/InstructExcel` at `0cea28a`.

InstructExcel is best treated as a **training/code-generation dataset**, not an office artifact benchmark.

- Data file: `instruct_excel_benchmark.json` with 10,520 examples.
- Inputs: spreadsheet metadata/context plus natural-language instruction.
- Outputs: OfficeScripts code.
- Evaluation code path: `experiment_code/run_few_shot.py`.
- Metrics: sacreBLEU, ROUGE, exact match, token F1, and parameter-normalized variants via `remove_params`.

### CUIF relevance

InstructExcel can help train NL-to-office-code models, but string similarity to reference code is a weak proxy for task success. CUIF should prefer execution/state validation and can use code similarity only as an auxiliary development metric.

## PPTC

**Primary source:** [GitHub](https://github.com/gydpku/PPTC), [arXiv](https://arxiv.org/abs/2311.01767).  
**Audited clone:** `/tmp/cuif_lit_repos/PPTC` at `277f56f`.

### Scope and properties

PPTC is a PowerPoint Task Completion benchmark with two task types:

- Create new slides;
- Edit PPT templates.

It explicitly simulates multi-turn dialogue. Each turn has a user instruction, a feasible API sequence, and a resulting label PPT.

Counts from the audited data:

- Create-new-slides: 229 sessions, 1,648 turns, 282 explicit spatial relation constraints, 59 unique APIs.
- Edit-PPT-template: 50 sessions, 160 turns, 21 spatial relation constraints, 26 unique APIs.

Typical evaluated operations include choosing slide areas, inserting text/pictures/tables/charts, changing font/background colors, setting font size, moving to slides, selecting textboxes/pictures, and deleting/inserting text.

### Evaluation pipeline

Code paths:

- `src/evaluate.py`
- `src/pptx_check.py`

Core function: `calc_acc(label_path, pred_path, instruction, additional_restrictions=[])`.

Pipeline:

1. Parse explicit position restrictions after `##` in instructions into tuples such as `(slide_id, object_A, object_B, relation)`.
2. Use `pptx_check.check` to evaluate spatial relations: left/top/right/bottom/center relations among slide objects or slide boundaries.
3. Extract text/style content from label and predicted PPTX via `ppt_reader.eval_get_contents(need_text=True, need_style=True, need_position=False)`.
4. Require exact string equality of extracted text+style.
5. Report:
   - turn-based mode (`--tf`): every turn compared against its label;
   - session-based mode (`--sess`): accumulated restrictions, final turn file compared;
   - `string_acc`, `position_acc`, average API cost, token cost.

### CUIF relevance

PPTC is direct evidence that multi-turn office-family benchmarks exist, but its tasks are relatively primitive/API-oriented, text-only, and evaluated with exact PPT structure/style plus simple position constraints. It does not evaluate practical open-ended office workflows, multimodal sketches/templates, or weighted partial progress.

## PPTC-R

**Primary source:** [GitHub](https://github.com/ZekaiGalaxy/PPTCR).  
**Audited clone:** `/tmp/cuif_lit_repos/PPTCR` at `080f0cc`.

PPTC-R extends PPTC with robustness perturbations:

- sentence-level robust paraphrases;
- semantic-level noisy instructions;
- language-level variants across 14 languages in the repo scripts/language list;
- API update/lack settings.

The evaluator remains essentially PPTC-style: compare turn/session PPTX outputs to labels with text/style equality and position checks.

### CUIF relevance

Useful for robustness and multilingual/noisy instruction ideas, but it does not address task complexity, visual multimodal constraints, or richer partial evaluation.

## PPTArena / PPTPilot (Michael Ofengenden et al.)

**Primary source:** [GitHub](https://github.com/michaelofengend/PPTArena), [arXiv](https://arxiv.org/abs/2512.03042), [Hugging Face paper page](https://huggingface.co/papers/2512.03042).  
**Audited clone:** `/tmp/cuif_lit_repos/PPTArena_michael` at `b5a5d59`.

### Scope and properties

The repo describes 100 decks, 2,125 slides, and 800+ targeted edits. The audited `src/evaluation_pairs_refined.json` has 100 cases with fields such as `prompt`, `style_target`, `original`, `ground_truth`, `category`, and `edit_type`.

Audited category counts:

- Content 67;
- Layout 29;
- Styling 29;
- Structure 15;
- Interactivity 4.

Audited edit-type examples:

- Text & Typography 29;
- Charts 10;
- Images & Pictures 10;
- Theme & Background 9;
- Alignment/Distribution/Z-order 8;
- Slide/Section Management & Footers 8;
- Tables 8;
- Shapes & Drawing 4;
- SmartArt & Diagrams 4;
- Slide Layout & Placeholders 3;
- smaller categories include accessibility, transitions, hyperlinks/action settings, template/master-level, audio/video, and object animations.

### Evaluation pipeline

Code paths:

- `run_evaluation.py`
- `src/llm/judge.py`

Pipeline:

1. Load agent outputs from `benchmark_results.json`.
2. Resolve original, predicted, and ground-truth decks.
3. Convert PPTX files to JSON structure with `pptx_to_json`.
4. Export slides to images.
5. Call `call_llm_judge` with user prompt, style target, initial/modified JSON, and images.
6. Save JSON results and generate an HTML report.

Judge details:

- **Instruction-following subscore (0--5):** uses structural JSON smart diffs (`diff_pptx_json`) and prompt-specific rubric. A perfect diff can receive 5; semantic equivalence and minor layout tolerances are allowed unless the instruction is exact.
- **Visual-quality subscore (0--5):** uses rendered slide images. For large decks, image similarity flags changed slides (SSIM/perceptual hash), then the VLM judges changed/affected slides in chunks and returns the minimum chunk score.
- Judges can use OpenAI or Gemini backends.

### CUIF relevance

This is the most directly relevant code-audited PowerPoint editing benchmark for multimodal artifact judging. It supports graded scores, separates instruction following from visual quality, and penalizes collateral visual damage. It does not provide multi-turn user interaction or per-turn trajectory scoring.

## PPTArena ICLR 2026 submission (Gandhi et al.)

**Primary source:** [OpenReview](https://openreview.net/forum?id=Dl1S4EvFwh).  
**Code audit status:** paper/source page only; no code clone audited here.

The OpenReview page describes 120 PowerPoint tasks across 12 files, covering presentation editing and content creation in PowerPoint Online. Its core contribution is a robust evaluation framework with task-specific, tree-structured rubrics that award partial credit, penalize unnecessary changes and poor aesthetics, and provide natural-language feedback. The OpenReview PDF snippet also states that evaluation depends on the original file and agent-modified file, not on the action sequence.

### CUIF relevance

This work is highly relevant and close to the proposed direction for partial credit in PPTX tasks. CUIF can still differentiate by emphasizing **multi-turn office-family tasks across PPTX/DOCX/XLSX**, **multimodal task instructions/constraints**, and **per-turn/trajectory-aware evaluation** rather than only final-file rubric grading.

## PPTAgent / DeepPresenter / PPTEval

**Primary source:** [GitHub](https://github.com/icip-cas/PPTAgent), [PPTAgent arXiv](https://arxiv.org/abs/2501.03936).  
**Audited clone:** `/tmp/cuif_lit_repos/PPTAgent` at `5327bbc`.

PPTAgent and DeepPresenter are presentation-generation agents rather than task-completion benchmarks. The repo includes a PPTEval evaluator:

- Code path: `pptagent/ppteval.py`.
- Render PPT to slide images.
- Use a vision model to describe slide style/content.
- Use a language model to score:
  - visual appeal/style (1--5);
  - content quality/relevance (1--5);
  - coherence/logical flow (1--5).
- Aggregate averages.

### CUIF relevance

PPTEval is useful for presentation quality dimensions and VLM-based slide assessment. It is not enough for instruction-following evaluation because it does not verify task-specific constraints, multi-turn changes, or precise artifact properties.

## OSWorld office tasks

**Primary source:** [GitHub](https://github.com/xlang-ai/OSWorld), [arXiv](https://arxiv.org/abs/2404.07972), [project page](https://os-world.github.io/).  
**Audited clone:** `/tmp/cuif_lit_repos/OSWorld` at `c7e54d2`.

OSWorld is a real desktop benchmark with multimodal observations. It includes office-like tasks for LibreOffice Impress/Calc/Writer and Windows Office-like files.

### Evaluation pipeline

Code paths:

- `desktop_env/desktop_env.py`
- `desktop_env/evaluators/metrics/slides.py`
- `desktop_env/evaluators/metrics/table.py`
- `desktop_env/evaluators/metrics/docs.py`

Pipeline:

1. Each task config specifies an evaluator with:
   - `func`: one metric or a list of metrics;
   - `conj`: `and` or `or` for combining multiple metrics;
   - result getter(s) and expected getter(s);
   - metric-specific `options`.
2. The environment applies post-config setup, fetches result and expected states/files, and runs metric functions.
3. If `conj=and`, any zero metric fails the task; otherwise metrics can be averaged or maxed depending on list/combinator path.

Office property coverage is broad:

- `compare_pptx_files`: slide count, backgrounds, notes, shapes, names, positions/sizes, images, text, paragraphs, bullet indentation, font names/sizes/bold/italic/color/underline/strike, alignment, tables/charts depending on object representation and options.
- `compare_table`: sheet names/data/print regions/fuzzy matching, sparklines, charts, styles, freeze panes, zoom, data validation, row/column props, filters, pivot tables, specific cells.
- `docs.py`: text exact/fuzzy/content-only checks, page breaks, default font, alignment, images/OCR/color, tables, and document-specific checks.

### CUIF relevance

OSWorld is a strong source of property-specific office evaluators and realistic visual GUI environment design. However, its task format is usually single user instruction with final-state grading. It does not natively grade turn-by-turn user updates or multimodal task constraints such as sketches/templates in the instruction.

## WindowsAgentArena office tasks

**Primary source:** [GitHub](https://github.com/microsoft/WindowsAgentArena), [arXiv](https://arxiv.org/abs/2409.08264), [OpenReview](https://openreview.net/forum?id=W9s817KqYf).  
**Audited clone:** `/tmp/cuif_lit_repos/WindowsAgentArena` at `6d39ed8`.

WindowsAgentArena is a scalable Windows desktop environment. Its task definitions are OSWorld-like: a task JSON provides instruction, setup config, evaluator function, and expected result. The run harness records trajectory HTML/JSON and then calls `env.evaluate()` to write `result.txt`; `show_result.py` aggregates domain success rates.

### CUIF relevance

It is valuable for Windows/PowerPoint/Excel/Word execution infrastructure and scalable evaluation on real apps. The evaluation model remains mostly final-state reward functions rather than multi-turn partial-credit office rubrics.

## What office-family benchmarks currently evaluate

| Property family | Strongest current coverage | Weakest current coverage |
|---|---|---|
| File existence/naming | OfficeBench, OdysseyBench | Almost universal but too shallow |
| Text content keywords | OfficeBench, OdysseyBench, DOCX parts of OSWorld | Semantics, grammar, preservation, revision quality |
| Excel values/formulas | SpreadsheetBench, OSWorld, SheetCopilot | Formula robustness under visual/style constraints; multi-turn spreadsheet editing |
| Excel formatting/charts/pivots | SheetCopilot, OSWorld | Cross-platform deterministic reproducibility |
| PPT text/style/position | PPTC, OSWorld | Open-ended edits, semantic equivalence, aesthetics |
| PPT visual quality | PPTArena, PPTEval | Per-turn and trajectory-aware visual scoring |
| DOCX formatting/layout | OSWorld | Rich task-specific semantic writing/revision and visual draft constraints |
| Cross-app workflows | OfficeBench, OdysseyBench | PPTX inclusion, fine-grained partial credit, multimodal instructions |
| User interaction | PPTC/PPTC-R, OdysseyBench chat histories | Dynamic clarification/correction turns with per-turn grading |
| Trajectory correctness | Mind2Web/tau2 outside office; not office benchmarks | Office-family expected intermediate states/action credit |

## Design implications for CUIF

1. **Use deterministic evaluators where possible, but expose scores at leaf level.** OfficeBench-like ANDing loses useful signal. Instead, report every check and aggregate into weighted subgoals.
2. **Build reusable property evaluators per artifact type.** OSWorld and SheetCopilot provide templates for PPTX/XLSX/DOCX property extraction. CUIF should normalize these into a single rubric schema.
3. **Treat rendered visual state as first-class.** PPTArena/PPTEval show that rendered slide/page images catch layout and aesthetics that XML comparisons miss.
4. **Support both final and per-turn expected artifacts.** PPTC already has turn labels; CUIF should generalize this to complex practical tasks with partial subgoals and user updates.
5. **Penalize collateral damage.** New benchmarks should check non-target slides/sheets/pages or source files, not only positive requirements.
6. **Use hidden test cases for spreadsheets and deterministic checks for known constraints.** SpreadsheetBench’s multi-test idea is strong for Excel formulas/data transformations.
7. **Use rubric generation carefully.** PPTArena ICLR and TheAgentCompany show rubric/checkpoint scoring can scale, but CUIF should keep rubrics inspectable, versioned, and benchmark-author-controlled.
