# Literature Review: Benchmarks for Computer-Use Instruction Following in Visual Office Artifacts

Date: 2026-04-13

This report surveys benchmarks and methods for computer-use agents and LLM/VLM agents that generate or edit visual office artifacts: presentations, spreadsheets, documents, PDFs, and related desktop workflows. The emphasis is on instruction following: explicit text constraints, visual constraints, local spatial references, style templates, preservation constraints, and multi-turn correction requests.

I inspected primary sources, project pages, and local benchmark code cloned under `.research/repos/`. The cloned repositories are intentionally gitignored.

## Executive Summary

The closest existing benchmark to the target idea is **PPTArena**, because it evaluates in-place PowerPoint editing under natural-language instructions, uses hidden `style_target` rubrics, separates instruction-following and visual-quality scores, and inspects both rendered slides and PPTX structure. **PPTC** and **PPTC-R** are also highly relevant because they explicitly encode PowerPoint positional restrictions and robustness perturbations, but their action space and tasks are simpler and more synthetic.

For full-deck generation, **PresentBench** is the strongest current rubric/checklist benchmark: 238 slide-generation instances, background materials, and an average of about 54 binary checklist items per instance. It is not primarily a CUA benchmark, but its checklist evaluation is a strong model for constraint-level scoring. **SlidesBench/AutoPresent**, **SlidesGen-Bench**, and **DeckBench** are useful for slide-generation/editing evaluation, especially visual/layout metrics and multi-turn revision, but they mostly measure reference similarity or broad slide quality rather than localized instruction compliance.

For spreadsheets, **SpreadsheetBench** and **SpreadsheetBench 2** are the most important current benchmarks. V1 focuses on real-world spreadsheet manipulation with online-judge-style multiple test cases. V2 moves closer to professional deliverables: financial modeling, debugging, templates, and visualization. Code inspection of V1 shows that many visual/style checks are not first-class. V2 adds VLM checklist scoring for chart visualizations, which is more aligned with visual constraint following. **SheetCopilot** and **SheetRM/SheetAgent** are useful earlier/parallel work for long-horizon spreadsheet manipulation, formatting, charts, and agent planning.

For documents, there is a gap in native Word/document artifact benchmarks. **DocEdit** and **DocEdit-v2** are very relevant for instruction following over document layouts, but they are document-image or HTML/CSS structure editing benchmarks rather than desktop CUA benchmarks. **OSWorld**, **WindowsAgentArena**, **OfficeBench**, and **OdysseyBench** include document and spreadsheet workflows, but their evaluators are mostly task-success, text containment, file existence, exact-match, or reference-state checks, not fine-grained visual instruction-following diagnostics.

The main opportunity is a benchmark that combines:

- A real desktop or file-editing environment.
- Initial artifact state plus text and visual instructions.
- Constraint-level ground truth with local spatial targets, style preservation, and negative constraints.
- Deterministic artifact parsers for PPTX/XLSX/DOCX/XML plus rendered-image checks.
- VLM judges only for constraints that cannot be deterministically measured.
- Scores reported per constraint type, not just per task.

## Scope and Methodology

I focused on benchmarks where the agent output is an artifact that can be viewed, edited, or inspected: PPTX/PDF slides, XLSX workbooks, DOCX/PDF documents, images, or office workflow outputs.

I used:

- Web and project-page review for up-to-date benchmark descriptions and leaderboards.
- Local code inspection of cloned repositories in `.research/repos/`.
- Evaluator inspection, because benchmark names often hide the most important detail: what is actually measured.
- Dataset/config inspection where task examples were included in the repo.

Cloned/inspected repositories:

- `xlang-ai/OSWorld`
- `microsoft/WindowsAgentArena`
- `zlwang-cs/OfficeBench`
- `microsoft/OdysseyBench`
- `RUCKBReasoning/SpreadsheetBench`
- `BraveGroup/SheetCopilot`
- `microsoft/InstructExcel`
- `cybisolated/SheetAgent`
- `para-lost/AutoPresent`
- `gydpku/PPTC`
- `ZekaiGalaxy/PPTCR`
- `PresentBench/PresentBench`
- `michaelofengend/PPTArena`
- `YunqiaoYang/SlidesGen-Bench`
- `morgan-heisler/DeckBench`
- `adobe-research/DocEdit-Dataset`

## Benchmark Map

| Benchmark | Artifact/domain | Environment/interface | Scale | Evaluation style | Instruction-following relevance |
| --- | --- | --- | --- | --- | --- |
| [OSWorld](https://os-world.github.io/) | Desktop apps including LibreOffice Calc, Impress, Writer | Real Ubuntu/Windows/macOS VM-style computer environment | 369 tasks in main release | Execution-based custom evaluators, reference files, success rates | Good broad CUA benchmark; office tasks exist, but constraints are usually folded into binary task success or reference comparison. |
| [WindowsAgentArena](https://microsoft.github.io/WindowsAgentArena/) | Windows apps including LibreOffice Calc/Writer, Paint, browser, files | Windows 11 VM in Docker/Azure | 154 Windows tasks | Deterministic custom scripts, domain success rates | Important for scalable Windows CUA, but office artifact scoring is still coarse. No PowerPoint/Impress tasks in the inspected `test_all.json`. |
| [OfficeBench](https://github.com/zlwang-cs/OfficeBench) | Office workflows over files, Excel, Word, PDF, email, calendar | API/tool transition system, not GUI pixels | 300 subtasks: 93 single-app, 95 two-app, 112 three-app | Exact match, fuzzy/text containment, file existence, Excel cell checks, calendar checks | Good for long-horizon office workflows, weak for visual artifact constraints and style/layout compliance. |
| [OdysseyBench](https://github.com/microsoft/OdysseyBench) | Long-horizon office workflows with memory/RAG | Tool/API office environment | 300 plus tasks, 302 neo tasks in repo | OfficeBench-style evaluators plus memory/query validation | Useful for memory-dependent instruction following, but not visual-output focused. |
| [SpreadsheetBench](https://spreadsheetbench.github.io/) | Real-world spreadsheet manipulation | Code/agent produces XLSX outputs | V1: 912 questions, 2,729 spreadsheets | Online-judge-style multiple test cases and answer regions | Strong functional manipulation benchmark; weak on style/visual constraints in V1 code. |
| [SpreadsheetBench 2](https://spreadsheetbench.github.io/) | End-to-end business spreadsheet workflows, financial modeling, debugging, visualization | Agent produces workbook deliverables | 224 real-world plus 97 synthetic samples on project page | Exact workbook/cell preservation for modeling/debugging; VLM checklist for charts | Much closer to deliverable-level spreadsheet instruction following, especially visualization checklists. |
| [SheetCopilot](https://github.com/BraveGroup/SheetCopilot) | Spreadsheet manipulation, formatting, charts, pivot tables | Excel/Google Sheets style action/API agent | 221 tasks over 28 workbooks | Reference workbook plus YAML checks using COM/win32; Exec@1 and Pass@1 | Relevant for spreadsheet operation following, including charts and formatting, but visual/style checks are partial. |
| [InstructExcel](https://github.com/microsoft/InstructExcel) | NL-to-OfficeScripts for Excel | Code generation/API | NL instruction plus OfficeScripts corpus | Code/semantic translation experiments | More NL-to-code than CUA or visual artifact evaluation. |
| [SheetRM/SheetAgent](https://sheetagent.github.io/) | Long-horizon spreadsheet reasoning/manipulation | Planner/Informer/Retriever agent using Python/openpyxl | Public release says 25 spreadsheets and 180 tasks | Repo mostly method/dataset release; experiments also use SheetCopilot | Useful SOTA method pattern for spreadsheet agents; less a visual benchmark. |
| [PPTC](https://github.com/gydpku/PPTC) | PowerPoint task completion, slide creation and template editing | API sequence generation and executor | Multi-turn sessions for create/edit tracks | PPTX-match: style/text comparison plus explicit positional relations | Highly relevant for constraint-following, especially spatial relations. Simpler and synthetic compared with real CUA. |
| [PPTC-R](https://github.com/ZekaiGalaxy/PPTC-R) | Robust PowerPoint task completion | API sequence generation | Robust/noisy/multilingual variants of PPTC-style tasks | Same PPTX evaluation family | Directly targets instruction robustness: paraphrase, noise, multilingual, and API-version perturbations. |
| [PPTArena](https://github.com/michaelofengend/PPTArena) | In-place PowerPoint editing | Agentic PPTX editing; web arena evaluator | 100 decks, 2,125 slides, 800+ targeted edits | Dual VLM-as-judge: instruction following and visual quality using structure diffs and slide images | Best current match for visual CUA instruction following in slides. |
| [SlidesBench/AutoPresent](https://github.com/para-lost/AutoPresent) | Single-slide generation/editable PPTX from instructions/images | Model generates Python/PPTX programs | 310 SlideShare decks, 300 train/10 test split | Block matching, text/color/position similarity, GPT-4o reference-free judge | Strong visual/layout generation benchmark; instruction constraints are implicit in target slide similarity. |
| [PresentBench](https://presentbench.github.io/) | Full slide decks from materials | Slide-generation agent outputs PDF/PPTX | 238 instances, average 54.1 binary checklist items | Fine-grained checklist, material-independent and material-dependent scoring with LLM/VLM judge | Excellent checklist design for instruction and content constraints, but not interactive CUA editing. |
| [SlidesGen-Bench](https://slidesgenbench.yqy314.top/) | AI-generated presentations | Product/model agnostic deck outputs | Slides-Align: 1,326 human preference rankings on project page | QuizBank content eval, aesthetics metrics, LLM rating, Arena ELO, PEI editability | Broad generated-presentation evaluation, including editability, but not localized instruction following. |
| [DeckBench](https://github.com/morgan-heisler/DeckBench) | Academic paper-to-slide generation and multi-turn slide editing | HTML/PDF generation/editing workflow | Metadata links and simulated multi-turn trajectories | Embedding similarity, layout heuristics, reference-free/reference-based metrics, LLM judge hooks | Useful for multi-turn slide revisions, but PDF/HTML-oriented and weak on atomic constraint pass/fail. |
| [DocEdit](https://github.com/adobe-research/DocEdit-Dataset) | Language-guided localized document editing | Document image plus command prediction | About 28K instances in full paper/dataset description | Predict executable edit command and bounding box | Very relevant to localized instruction following over document layouts, but not desktop CUA and partial public release. |
| [DocEdit-v2](https://aclanthology.org/2024.emnlp-main.867.pdf) | Multimodal document structure editing | HTML/CSS document editing from visual examples | Paper benchmark, not cloned here | Human/VLM-style judgments for instruction adherence and style replication | Strong conceptual fit for visual/layout editing constraints, adjacent rather than office-agent benchmark. |
| [OSUniverse](https://agentsea.github.io/osuniverse/) | Multimodal GUI navigation and desktop tasks | Desktop-oriented benchmark | 160 tasks across 5 levels and 9 categories | YAML tasks, validators over text output, screenshot, trajectory, bash command | Useful adjacent CUA benchmark; not office-artifact centered. |

## SOTA Snapshot by Benchmark

This table is a 2026-04-13 snapshot from the primary sources I could inspect. Leaderboards for fast-moving agent benchmarks change often, so treat these as orientation rather than archival numbers.

| Benchmark | Current or reported strong method | Reported signal | Takeaway |
| --- | --- | --- | --- |
| OSWorld | Specialized GUI/CUA models and agentic frameworks using screenshots, accessibility trees, set-of-marks, and GUI grounders | Original project page reports best model 12.24 percent versus humans 72.36 percent in the paper-era results; OSWorld-Verified now maintains updated results on the official site | General CUA remains hard; office tasks are a subset, not the main driver. |
| WindowsAgentArena | Navi with OmniParser/UIA-style screen parsing | Project page reports Navi at 19.5 percent versus 74.5 percent human performance | Screen parsing and UI grounding are bottlenecks even before artifact-quality scoring. |
| OfficeBench | GPT-4o in the README leaderboard | 47.00 overall across 300 tasks in the inspected README | Strong language models help, but three-app workflows remain difficult. |
| OdysseyBench | HomerAgents+/Neo and memory/RAG configurations in the repo | README emphasizes raw-chat versus RAG modes rather than a static public leaderboard | Main SOTA question is memory retrieval and task grounding, not visual artifact fidelity. |
| SpreadsheetBench V1 | Spreadsheet products and agent systems on the public leaderboard | Project page lists high V1 leaderboard scores, while the original paper emphasizes a large gap to experts | V1 is increasingly a product benchmark, but style/visual scoring is still limited. |
| SpreadsheetBench 2 | Claude Opus 4.6 with Bash Agent on the V2 full leaderboard | Project page lists 34.89 percent V2 full score | End-to-end business spreadsheet workflows are still far from solved, especially debugging and preservation. |
| SheetCopilot | GPT-4 for Pass@1 on the 20-sample subset; GPT-3.5-Turbo full-dataset run in README | GPT-4 Pass@1 55.0 on 20 samples; GPT-3.5-Turbo Pass@1 44.3 full dataset | Early spreadsheet agents execute often but fail semantic correctness frequently. |
| SheetRM/SheetAgent | SheetAgent Planner/Informer/Retriever | Project page reports 20-30 percent pass-rate improvements over baselines across multiple benchmarks | Retrieval over workbook structure is a useful pattern for spreadsheet instruction following. |
| PPTC/PPTC-R | Closed LLMs such as GPT-4 are the natural high-performing baselines in the repo setup | Results are image-heavy in README; code supports closed and open LLM evaluation | Their contribution is constraint/robustness design more than a modern leaderboard. |
| PPTArena | PPTPilot | README reports more than 10 percentage-point gains over proprietary agents and frontier VLM systems | Strongest current method pattern for slide editing: structure-aware planning plus deterministic XML operations plus verification. |
| AutoPresent/SlidesBench | AutoPresent program-synthesis/refinement pipeline | Paper/repo frame AutoPresent against baseline slide-generation methods | Editable programmatic generation is a useful baseline for visual template following. |
| PresentBench | NotebookLM | README says NotebookLM significantly outperforms other slide-generation methods | Material-grounded slide generation has moved quickly, but this is not interactive editing. |
| SlidesGen-Bench | Product/model arena rather than one SOTA method | Project page emphasizes ELO/preference, QuizBank, aesthetics, and editability | Useful for product-level deck generation comparison, less for localized constraints. |
| DeckBench | Baseline HTML editor plus custom agent interface | Repo provides evaluation and simulation framework, not a definitive SOTA leaderboard | Useful for multi-turn academic-deck workflows and relative improvement metrics. |
| DocEdit/DocEdit-v2 | DocEditor and multimodal document-structure editors | DocEdit README reports its model outperforming baselines by 15-18 percent | Localized document edit prediction is highly relevant to future DOCX/PDF instruction benchmarks. |
| OSUniverse | OpenAI computer-use-preview in project-page table | Project page reports 47.80 total score for computer-use-preview-2025-03-11 | Specialized computer-use models can lead broad GUI navigation, but hardest levels remain weak. |

## Deep Dives and Code Inspection

### OSWorld

Primary sources: [project page](https://os-world.github.io/), [GitHub](https://github.com/xlang-ai/OSWorld), [paper](https://arxiv.org/abs/2404.07972).

OSWorld is the canonical broad CUA benchmark for real computer environments. The project page describes 369 real-world computer tasks and 134 execution-based evaluation functions. The inspected local task split in `.research/repos/OSWorld/evaluation_examples/test_all.json` contains:

- `chrome`: 46
- `gimp`: 26
- `libreoffice_calc`: 47
- `libreoffice_impress`: 47
- `libreoffice_writer`: 23
- `multi_apps`: 101
- `os`: 24
- `thunderbird`: 15
- `vlc`: 17
- `vs_code`: 23

Total: 369 tasks.

Code-level observations:

- `show_result.py` aggregates office success over Calc, Impress, and Writer.
- LibreOffice Impress tasks often compare the final PPTX against one or more gold PPTX files with `compare_pptx_files`.
- `.research/repos/OSWorld/desktop_env/evaluators/metrics/slides.py` uses `python-pptx` to inspect slide count, backgrounds, notes, shape counts, geometry, text, tables, font name/size/bold/italic/color/underline, and other shape-level properties.
- `.research/repos/OSWorld/desktop_env/evaluators/metrics/table.py` supports spreadsheet rules such as sheet data, print settings, chart, style, pivot table, freeze/filter, and cell checks.

Instruction-following implications:

OSWorld is excellent for testing whether an agent can operate a real desktop, recover state, and complete an office task. It is less diagnostic for instruction following. A task like "duplicate the last two slides in alternating order" becomes a binary or near-binary reference comparison. The benchmark generally does not expose per-constraint outcomes such as "duplicated the right slides", "preserved layout", "preserved animations", "did not alter earlier slides", or "followed top-right image constraint".

### WindowsAgentArena

Primary sources: [project page](https://microsoft.github.io/WindowsAgentArena/), [GitHub](https://github.com/microsoft/WindowsAgentArena), [paper](https://arxiv.org/abs/2409.08264).

WindowsAgentArena adapts the OSWorld-style environment to scalable Windows 11 VMs. The project page reports 154 tasks and 19.5 percent success for Navi versus 74.5 percent for humans in the initial paper setting.

Local task split inspected at `.research/repos/WindowsAgentArena/src/win-arena-container/client/evaluation_examples_windows/test_all.json`:

- `chrome`: 17
- `clock`: 4
- `file_explorer`: 19
- `libreoffice_calc`: 24
- `libreoffice_writer`: 19
- `microsoft_paint`: 3
- `msedge`: 13
- `notepad`: 2
- `settings`: 5
- `vlc`: 21
- `vs_code`: 24
- `windows_calc`: 3

Total: 154 tasks.

Code-level observations:

- `show_result.py` reports per-domain success rates and an Office aggregate, though the Windows task set inspected includes Calc and Writer but not Impress.
- The benchmark has a "hard" difficulty mode where agents must initialize/setup more of the task themselves.
- The environment emphasizes scalable parallel execution and screen parsing. Navi uses combinations of UI Automation, OCR, icon detection, DOM parsing for browsers, and OmniParser.

Instruction-following implications:

WindowsAgentArena is valuable if the target benchmark must run in Windows with realistic apps. It is less directly useful for artifact-level visual constraints because the current office tasks are mostly Calc/Writer and deterministic endpoint checks, not rich layout/rubric scoring.

### OfficeBench

Primary source: [GitHub](https://github.com/zlwang-cs/OfficeBench).

OfficeBench evaluates language agents across office workflows involving multiple applications. It is formulated as a transition system: current application is state, operations are transitions. It is not a pixel-level desktop CUA benchmark.

Local repository stats:

- 300 subtasks total.
- 93 single-app tasks.
- 95 two-app tasks.
- 112 three-app tasks.

Evaluator functions counted in local configs:

- `evaluate_contain`: 279
- `evaluate_file_exist`: 233
- `evaluate_excel_cell_value`: 37
- `evaluate_not_contain`: 19
- `evaluate_exact_match`: 18
- `evaluate_diff_contain_text`: 6
- `evaluate_calendar_no_overlap`: 6
- `evaluate_file_not_exist`: 2
- `evaluate_excel_cell_comparator`: 1

Code-level observations:

- `.research/repos/OfficeBench/utils/evaluate.py` reads XLSX/DOCX/PDF/TXT/ICS/email outputs and applies containment, exact match, file existence, Excel cell checks, and calendar overlap checks.
- Many generation tasks only check that a file exists or contains keywords. Example: `tasks/3-59/subtasks/0.json` asks for a teaching report in DOCX and PDF but only checks file existence.
- Word-document tasks may only check text containment. Example: `tasks/1-15/subtasks/2.json` checks that expected reference keywords appear in `project_report.docx`.

Instruction-following implications:

OfficeBench is strong for workflow composition and app switching, but weak for visual output compliance. It would not detect many common instruction-following failures such as wrong font, broken layout, wrong image size, poor visual hierarchy, or undesired extra edits.

### OdysseyBench

Primary source: [GitHub](https://github.com/microsoft/OdysseyBench), [paper identifier in README: arXiv 2508.09124](https://arxiv.org/abs/2508.09124).

OdysseyBench extends OfficeBench-style workflows toward long-horizon memory and retrieval. It includes OdysseyBench+ and OdysseyBench-Neo tracks, with chat histories and query/memory separation.

Local repository stats:

- `subtasks_plus`: 300 tasks, distributed like OfficeBench: 93 single-app, 95 two-app, 112 three-app.
- `subtasks_neo`: 302 tasks, with 60 single-app, 71 two-app, 171 three-app.

Evaluator functions are similar to OfficeBench. The Neo track increases Excel cell checks:

- `evaluate_contain`: 314
- `evaluate_file_exist`: 234
- `evaluate_excel_cell_value`: 107
- `evaluate_not_contain`: 10

Code-level observations:

- `.research/repos/OdysseyBench/evaluation/task_evaluator.py` loads per-task settings and evaluates each configured criterion.
- `llm-as-a-judge.py` judges information leakage and completeness of query plus chat logs, not final artifact visual fidelity.
- Example `tasks/3-77/subtasks_neo/10.json` asks for a DOCX prediction in a precise sentence format. The evaluator checks file existence and broad keywords, not exact numeric answer or formatting.

Instruction-following implications:

OdysseyBench matters if a future CUA instruction-following benchmark includes hidden user preferences scattered in long histories. It does not solve the visual artifact scoring problem.

### SpreadsheetBench and SpreadsheetBench 2

Primary sources: [project page and leaderboard](https://spreadsheetbench.github.io/), [GitHub](https://github.com/RUCKBReasoning/SpreadsheetBench), [OpenReview paper](https://openreview.net/forum?id=xom4egdtbB).

SpreadsheetBench V1 is the strongest public benchmark for real-world spreadsheet manipulation from Excel forum tasks. It contains 912 questions and 2,729 spreadsheet test cases. Its central evaluation idea is online-judge style robustness: a correct solution should generalize across multiple test-case workbooks, not just solve a single concrete file.

SpreadsheetBench 2, described on the same project page, moves toward end-to-end professional spreadsheet workflows:

- 224 real-world samples and 97 synthetic samples.
- Categories: financial modeling/template, debugging, visualization.
- Average 11.8 sheets and 593.5 modified cells on the project page.
- Financial modeling/template/debugging are exact final-workbook tasks where all required cell modifications must be accurate and unchanged cells must remain unmodified.
- Visualization tasks use a reference answer with a checklist of assertions and VLM pass/fail judgments over chart images.

As of the project page snapshot inspected on 2026-04-13, the V2 leaderboard lists Claude Opus 4.6 with a Bash Agent scaffold as the top verified V2 full score at 34.89 percent, with strong visualization but weak debugging. The page also lists product and V1 leaderboard tracks separately, so leaderboard numbers should be checked directly before quoting in a paper.

Code-level observations for V1:

- `.research/repos/SpreadsheetBench/evaluation/evaluation.py` loads ground truth and processed workbooks with `openpyxl.load_workbook(..., data_only=True)`.
- `cell_level_compare` compares cell values in `answer_position`.
- Fill-color and font-color comparisons exist in code but are commented out.
- Evaluation computes a multi-test-case pass condition using `soft_restriction` and `hard_restriction`.
- `.research/repos/SpreadsheetBench/evaluation/parity_test.py` handles formula recalculation parity between LibreOffice and Windows Excel/win32com pipelines.
- Inference prompts produce Python code to manipulate spreadsheets, with single-round and multi-round ReAct/execution-feedback variants.

Instruction-following implications:

SpreadsheetBench V1 is excellent for functional robustness, but code inspection shows it under-measures style and visual instructions. If an instruction says "highlight matching rows" or "format as Accounting Special", V1-style answer-region cell-value comparison may miss failures. SpreadsheetBench 2's chart checklist approach is much closer to the desired benchmark, especially for visualization instructions.

### SheetCopilot

Primary sources: [GitHub](https://github.com/BraveGroup/SheetCopilot), [paper](http://arxiv.org/abs/2305.19308).

SheetCopilot is an early and important spreadsheet-agent benchmark and agent framework. It contains 221 tasks over 28 workbooks, with 44 operations across entry/manipulation, management, formatting, chart, and pivot-table categories.

Reported README results:

- On a 20-sample subset, GPT-4 has 55.0 percent Pass@1 and GPT-3.5-Turbo has 45.0 percent Pass@1.
- On the full dataset, GPT-3.5-Turbo has 87.3 percent Exec@1 and 44.3 percent Pass@1.

Code-level observations:

- `.research/repos/SheetCopilot/agent/evaluation.py` compares generated workbooks against one or more reference solutions and YAML checks.
- `.research/repos/SheetCopilot/agent/utils/eval.py` uses Excel COM/win32 to compare workbooks and features such as cells, charts, pivot tables, filters, and format conditions.
- Cell formatting comparison code is present but much of it is commented out.
- YAML checks can explicitly require APIs and condition formatting. Example: a BoomerangSales task checks `format_conditions` and requires `SetConditionalFormat`.

Instruction-following implications:

SheetCopilot is relevant because it includes formatting, charts, and pivot tables, not just formula cells. But its visual evaluation is still incomplete and Windows-COM dependent. It is a good source of operation taxonomy, less a complete answer for visual instruction-following evaluation.

### InstructExcel

Primary source: [GitHub](https://github.com/microsoft/InstructExcel), [paper](https://arxiv.org/abs/2310.14495).

InstructExcel pairs natural-language Excel instructions with OfficeScripts code. Its importance is in mapping user language to executable spreadsheet operations. It is not primarily a computer-use or visual artifact benchmark.

Instruction-following implications:

InstructExcel can inform API-action taxonomies and data generation for Excel instructions. It should not be treated as an output-artifact fidelity benchmark.

### SheetRM and SheetAgent

Primary sources: [project page](https://sheetagent.github.io/), [GitHub](https://github.com/cybisolated/SheetAgent), [paper](https://arxiv.org/abs/2403.03636).

SheetAgent proposes a Planner/Informer/Retriever architecture for spreadsheet reasoning and manipulation. The SheetRM dataset release in the repo includes 25 spreadsheets and 180 tasks, about 60 percent of the full dataset according to the README.

Code-level observations:

- The planner prompt enforces step-by-step Python/openpyxl actions.
- The Informer retrieves spreadsheet sub-tables using SQL over sheet representations.
- Prompt examples include visual/style tasks such as highlighting rows in red and formatting columns as currency.

Instruction-following implications:

SheetAgent is mainly a method contribution. Its architecture is a useful baseline for future spreadsheet instruction-following benchmarks: plan, retrieve table context, execute small openpyxl actions, observe, and iterate.

### PPTC

Primary source: [GitHub](https://github.com/gydpku/PPTC).

PPTC is a PowerPoint task-completion benchmark with two task types: creating new slides and editing PPT templates. It simulates multi-turn dialogue sessions. Each turn contains a user instruction, feasible API sequence, and label output file.

Code-level observations:

- `.research/repos/PPTC/PPT_test_input/Create_new_slides/session_0.json` encodes multi-turn slide creation with user instructions and feasible API solutions.
- `.research/repos/PPTC/PPT_test_input/Edit_PPT_template/session_0.json` includes deck-wide edits such as title colors, background changes, image rotation, and image width.
- `.research/repos/PPTC/src/evaluate.py` computes turn/session accuracy and calls `calc_acc`.
- `calc_acc` parses additional position restrictions marked with `##`, checks them with `pptx_check.check`, and compares serialized content/style from label and prediction files.
- `.research/repos/PPTC/src/pptx_check.py` implements spatial relations: left, top, right, bottom, center, and object-to-object relations.

Instruction-following implications:

PPTC is one of the most relevant early benchmarks for explicit constraints. It can encode relational layout assertions such as "object A is left of object B" or "title is at the top". Its limitation is that it is API-centric and comparatively synthetic; it does not evaluate rich visual templates, preservation constraints, or real office GUI interaction at modern scale.

### PPTC-R

Primary source: [GitHub](https://github.com/ZekaiGalaxy/PPTC-R).

PPTC-R extends PPTC toward robustness. It includes:

- Instruction perturbations: sentence-level, semantic, noisy instructions.
- Multilingual instructions: Arabic, Bulgarian, Chinese, English, French, German, Greek, Hindi, Russian, Spanish, Swahili, Thai, Turkish, Urdu, Vietnamese.
- API/software changes: `api_update` and `api_lack`.

Code-level observations:

- `main.py` exposes `--robust`, `--noisy`, `--language`, `--api_lack`, and `--api_update`.
- `src/utils.py` selects datasets based on robustness/noise/language/API setting.
- `test/short/noisy.txt` adds irrelevant distractions around original instructions.
- `test/short/robust*.txt` includes paraphrase and semantic variants.

Instruction-following implications:

PPTC-R is directly relevant to instruction robustness. It does not solve visual output evaluation, but it provides a useful perturbation recipe for a future CUA instruction-following benchmark.

### PPTArena

Primary sources: [GitHub](https://github.com/michaelofengend/PPTArena), [paper](https://arxiv.org/abs/2512.03042).

PPTArena is the closest benchmark to the user's intended benchmark direction. It evaluates agentic PowerPoint editing across 100 decks, 2,125 slides, and 800+ targeted edits covering text, charts, tables, animations, and master-level styles. Each case includes an original deck, a ground-truth deck, a user prompt, and a hidden/richer `style_target`.

Reported method:

- **PPTPilot** is the proposed method.
- It plans semantic edit sequences.
- It routes between high-level programmatic tools and deterministic XML operations.
- It verifies outputs through an iterative plan-edit-check loop.
- The README reports more than 10 percentage-point improvement over strong proprietary agents and frontier VLM systems, especially on compound, layout-sensitive, and cross-slide edits.

Code-level observations:

- `.research/repos/PPTArena/src/evaluation_pairs_refined.json` contains each task's `prompt`, `style_target`, `original`, `ground_truth`, `category`, `enhancement_notes`, and `edit_type`.
- Tasks include precise constraints such as increasing all non-title font sizes by exactly 2 pt, preserving formatting/layout during translation, rotating and positioning photos, chart/table changes, animations, and master-level style edits.
- `.research/repos/PPTArena/src/llm/judge.py` splits evaluation into instruction-following and visual-quality judgments.
- The instruction judge uses JSON structure diffs between ground truth and prediction, optionally with the initial JSON, plus the hidden `style_target`.
- The visual judge compares rendered slide images and uses SSIM/pHash heuristics to identify differing slides before VLM judgment on large decks.
- `.research/repos/PPTArena/src/ppt/analysis.py` parses PPTX into JSON, including slide backgrounds, shapes, geometry, rotation, z-order, text runs, typography, tables, charts, fill/line/shadow, placeholders, and hyperlinks.

Important reproducibility caveat from code inspection:

- The Flask arena route appears to use `ground_truth` correctly.
- The bulk `run_evaluation.py` path appears to set `gt_json` and `gt_imgs` from `case.get("original")` rather than `case["ground_truth"]`. That would compare predictions against the original deck in the bulk script. This should be checked or fixed before relying on bulk scores.

Instruction-following implications:

PPTArena is the most direct template for a new benchmark. Its hidden `style_target` is a strong idea: the public prompt can be natural, while evaluation criteria remain precise. The main weaknesses are VLM judge reliability, possible script inconsistency, and restriction to PowerPoint editing.

### SlidesBench and AutoPresent

Primary sources: [GitHub](https://github.com/para-lost/AutoPresent), [paper](https://www.arxiv.org/abs/2501.00912).

AutoPresent introduces SlidesBench and a structured program-synthesis approach to slide generation. SlidesBench includes 310 SlideShare decks, with 300 train decks and 10 test decks. It supports settings such as sufficient instruction, visual absence, and creative generation.

Code-level observations:

- `slidesbench/seed_instruction.py` uses GPT-4o-mini to create high-level instructions from slide images.
- `evaluate/page_eval.py` parses PPTX into blocks with normalized positions and sizes and uses matching to compute text, color, and position similarity.
- `evaluate/reference_free_eval.py` uses GPT-4o as a VLM judge over rendered slide images and extracted slide text, scoring text/image/layout/color.
- The method encourages generating editable PPTX via Python programs such as `code_pptx.py` and `code_library.py`.

Instruction-following implications:

SlidesBench is strong for visual similarity and editable slide generation. It is less explicit about constraint-level instruction compliance because the target slide is the primary signal. It is valuable for visual template following and layout metrics.

### PresentBench

Primary sources: [project page](https://presentbench.github.io/), [GitHub](https://github.com/PresentBench/PresentBench), [paper](https://arxiv.org/pdf/2603.07244).

PresentBench is a recent fine-grained rubric benchmark for slide generation. The README and project page describe:

- 238 instances.
- Background materials from sources such as papers, textbooks, and financial reports.
- An average of 54.1 binary checklist items per instance.
- Five domains: academia, advertising, economics, education, and talk.
- Strong reported performance for NotebookLM relative to other slide-generation methods.

Code-level observations:

- `utils/generate_checklist.py` generates material-independent and material-dependent checklist items.
- `utils/judge_utils.py` loads common and case-specific JSON judge prompts, including deterministic callables where needed.
- `judge.py` converts PPTX to PDF when necessary, uploads slides/materials to Gemini-like judges, and evaluates checklist items as yes/no/not applicable.
- `scoring.py` separately scores material-independent and material-dependent sections using class weights and computes valid counts, yes counts, NA counts, and leave-one-out stats.

Instruction-following implications:

PresentBench is not a CUA benchmark and focuses on creating decks from materials rather than editing existing artifacts. But its checklist design is highly relevant: future CUA benchmarks should expose scores by atomic constraint rather than only whole-task success.

### SlidesGen-Bench

Primary sources: [project page](https://slidesgenbench.yqy314.top/), [GitHub](https://github.com/YunqiaoYang/SlidesGen-Bench), [paper](https://arxiv.org/abs/2601.09487).

SlidesGen-Bench evaluates heterogeneous AI presentation products and systems. It emphasizes universality, quantification, and reliability.

Key components from README/project inspection:

- Slides-Align dataset: 1,326 human preference rankings, 9 products, 7 categories, 187 topics.
- Content evaluation via QuizBank.
- Aesthetics metrics: figure-ground contrast, color harmony, colorfulness, subband entropy, visual heart-rate variability style metric.
- LLM rating and LLM Arena pairwise ELO.
- Presentation Editability Intelligence (PEI) using a knock-out strategy.

Instruction-following implications:

SlidesGen-Bench is good for comparing deck generation products and introduces editability as a metric. It is less focused on whether a model obeyed specific user constraints.

### DeckBench

Primary source: [GitHub](https://github.com/morgan-heisler/DeckBench), [paper link in README](https://arxiv.org/abs/2602.13318).

DeckBench evaluates academic paper-to-slide generation and multi-turn slide editing. It is designed around a realistic workflow: generate a deck from a paper, then iteratively edit the deck with natural-language requests generated by a simulated user.

Code-level observations:

- `simulation_pipeline/multiturn_simulation.py` generates multi-turn editing trajectories.
- `simulation_pipeline/custom/editor_agent.py` is a baseline HTML slide editor.
- `generation_evaluation.py` and `multiturn_evaluation.py` compare generated/edited PDF slide decks against reference slides and papers.
- `metrics/slide_metrics.py` computes reference-free metrics such as perplexity, paper faithfulness, element-in-canvas, overlap-free layout, and title-vs-bullet font-size heuristics.
- It also computes reference-based text, visual, combined, and positional similarity using embeddings and order-aware Hungarian matching.

Instruction-following implications:

DeckBench is valuable for multi-turn revision and realistic paper-to-deck workflows. It is less ideal for native CUA instruction following because the baseline editing workflow is HTML/PDF-oriented and metrics are broad rather than atomic constraint pass/fail.

### DocEdit and DocEdit-v2

Primary sources: [DocEdit Dataset GitHub](https://github.com/adobe-research/DocEdit-Dataset), [DocEdit-v2 paper](https://aclanthology.org/2024.emnlp-main.867.pdf).

DocEdit proposes language-guided localized document editing: given a document image and open-vocabulary edit request, the system predicts a software-executable command and bounding box. The full dataset is described as about 28K instances over PDFs and design templates. The public repo is a partial release with original image, user request, and output command for train/validation splits of the DocEdit-PDF subset.

Instruction-following implications:

DocEdit is conceptually important because it treats instructions as localized operations over document objects. It directly addresses direct and indirect references to text and visual objects such as paragraphs, lists, and tables. A future CUA benchmark can adapt this idea to native DOCX/PPTX/XLSX artifacts: target object, operation, constraint arguments, and bounding box/region references.

DocEdit-v2 extends this family toward multimodal document structure editing and style replication in HTML/CSS-like representations. It is adjacent to office artifact generation, especially for evaluating instruction adherence and style replication, but not a desktop CUA benchmark.

## State-of-the-Art Method Patterns

### General desktop CUA

The dominant methods are multimodal planner-grounder systems:

- A planner model reasons over task state and prior actions.
- A screen parser or grounding model maps planned actions to UI elements or coordinates.
- Agents use screenshots, accessibility trees, DOM trees, OCR, set-of-marks, and sometimes specialized GUI grounding models.
- Verification is usually external endpoint evaluation rather than internal constraint checking.

Representative systems:

- OSWorld baselines include GPT/Gemini/Claude families, UI-TARS, Agent-S, Qwen/CogAgent-style VLMs, and set-of-marks approaches.
- WindowsAgentArena's Navi combines chain-of-thought planning with UIA/DOM/OCR/icon detections and OmniParser-style screen understanding.
- OSUniverse reports strong results for specialized computer-use models such as OpenAI computer-use-preview in its project page, with large remaining gaps on hardest task levels.

### Slides and PowerPoint

The strongest emerging pattern is structure-aware editing:

- Parse PPTX into a structured representation.
- Plan semantic edits.
- Use high-level libraries for common operations.
- Fall back to deterministic XML manipulation for precise control over animations, masters, charts, or layout.
- Render and compare outputs.
- Iterate with a plan-edit-check loop.

PPTArena/PPTPilot is the clearest example. AutoPresent also uses program synthesis to generate editable PPTX rather than raster-only slides. PresentBench, SlidesGen-Bench, and DeckBench shift evaluation toward rubric/checklist, preference, and editability metrics.

### Spreadsheets

The dominant methods are code-generating or tool-using spreadsheet agents:

- Generate Python/openpyxl/xlwings/OfficeScripts code.
- Use spreadsheet summaries or schema extraction to fit context windows.
- Execute code and feed back errors or partial observations.
- Retrieve relevant tables or cells via SQL/RAG-like mechanisms.
- Verify cell values, formulas, charts, and sometimes workbook state.

Representative systems:

- SpreadsheetBench uses single-round and multi-round inference with execution feedback and ReAct-style prompts.
- SheetCopilot uses an action API and evaluates execution/pass rates.
- SheetAgent combines Planner, Informer, and Retriever modules.
- SpreadsheetBench 2's leaderboard suggests frontier models still struggle with full business workflows, especially debugging and preservation.

### Documents

Document editing methods are split:

- OfficeBench/OdysseyBench-style tools can read/write DOCX/PDF and check keyword/file outcomes.
- DocEdit-style systems localize requested changes in document images and predict edit commands.
- DocEdit-v2-style systems edit document structure representations and evaluate instruction adherence/style replication.

Native Word/DOCX CUA benchmarks are much less mature than slides and spreadsheets.

## Instruction-Following and Constraint-Focused Benchmarks

The most relevant instruction/constraint-focused benchmarks are:

1. **PPTArena**: explicit natural-language editing prompts plus hidden precise `style_target`; separate instruction-following and visual-quality scores; structure diff plus rendered images.
2. **PPTC**: multi-turn PowerPoint instructions with explicit spatial-relation restrictions.
3. **PPTC-R**: robustness variants over PPTC: noisy, paraphrased, multilingual, API-lack/API-update conditions.
4. **PresentBench**: fine-grained checklist evaluation, especially useful as a rubric model for content and slide quality constraints.
5. **SpreadsheetBench 2 visualization track**: checklist assertions judged by VLM over chart images.
6. **DocEdit/DocEdit-v2**: localized document edit requests and style/layout adherence, adjacent to CUA.

Benchmarks that are less constraint-focused but still useful:

- OSWorld and WindowsAgentArena: good for real computer-use execution and artifact endpoint comparison.
- SpreadsheetBench V1: good for functional correctness and robustness across test cases, weak for visual/style constraints.
- SheetCopilot: includes operation/formatting/chart checks but is partial and platform-specific.
- SlidesBench/AutoPresent: visual target similarity rather than explicit instruction checklist.
- SlidesGen-Bench and DeckBench: broad deck quality, multi-turn revision, editability, and similarity, but not atomic constraints.
- OfficeBench/OdysseyBench: office workflow and memory, weak visual artifact fidelity.

## Evaluation Design Lessons

### 1. Reference files are useful but insufficient

Gold PPTX/XLSX/DOCX files make evaluation reproducible, but they can collapse many constraints into one score. They also penalize valid alternative layouts if the benchmark expects a single reference. PPTArena improves this by combining reference comparison with a hidden style target and VLM judgment. PresentBench improves it by using many binary checklist items.

Recommendation: use reference artifacts as one evaluation input, but report atomic constraints separately.

### 2. Visual constraints require both object parsing and rendering

Artifact XML alone can miss visual effects. Rendered images alone can miss editability, hidden structure, formulas, charts, and masters. The best designs combine:

- Native file inspection: PPTX XML, DOCX XML, XLSX workbook parts.
- Library-level parsing: python-pptx, openpyxl, python-docx, libreoffice conversion.
- Rendered images: per-slide/page/chart screenshots.
- OCR/object detection where needed.
- VLM judge only for ambiguous semantic or aesthetic criteria.

### 3. Preservation constraints must be first-class

Many office edits require "change X, preserve everything else." Existing benchmarks often score the final artifact against a target but do not distinguish:

- Changed the requested object.
- Preserved unrelated objects.
- Avoided extra edits.
- Maintained editable structure.
- Preserved formulas, links, charts, notes, masters, accessibility metadata.

SpreadsheetBench 2 explicitly says unchanged cells must remain unmodified. PPTArena's structure diff can identify unexpected changes. This should be generalized.

### 4. Spatial language needs typed tolerances

User instructions like "make the top-right image bigger" require:

- Region identification: top-right relative to slide/page/canvas.
- Object identification: image versus icon versus chart.
- Operation: enlarge.
- Degree: bigger by a qualitative or quantitative amount.
- Constraints: preserve aspect ratio, avoid overlap, keep within bounds.

PPTC has useful relative-position checks, but future benchmarks need continuous tolerances for coordinates, size, alignment, margins, and overlap.

### 5. VLM-as-judge should be scoped and auditable

PPTArena, PresentBench, SlidesGen-Bench, DeckBench, and SpreadsheetBench 2 all use some LLM/VLM evaluation. This is unavoidable for aesthetics and semantic content, but dangerous for reproducibility.

Recommendation:

- Use deterministic checks wherever possible.
- Use VLM judges only for constraints that cannot be measured structurally.
- Store prompts, model versions, images, and rationales.
- Use multiple judges or adjudication for ambiguous items.
- Report judge failure/NA rates.
- Keep checklist assertions specific and binary.

### 6. Multi-turn editing is underdeveloped

PPTC/PPTC-R and DeckBench include multi-turn settings. Most other benchmarks are single-turn. Real instruction following often involves corrections:

- "No, keep the old font."
- "Only apply that to slide 3."
- "Make it match this template."
- "The chart is too small; enlarge it but keep the title visible."

A future benchmark should include cumulative-state scoring and regression checks after each turn.

## Gaps in the Literature

### Gap 1: No benchmark unifies CUA control with artifact-level visual instruction scoring

OSWorld/WAA test real computer use but do not deeply score visual artifacts. PPTArena deeply scores PPTX editing but is not a general desktop CUA benchmark. A new benchmark can occupy this missing intersection.

### Gap 2: Native DOCX/document visual editing is undercovered

There is good adjacent work in DocEdit and DocEdit-v2, but little for native Word/DOCX visual instruction following with fonts, headings, tables, images, page layout, comments, tracked changes, and PDF export fidelity.

### Gap 3: Visual instructions are rarely used as inputs

Most benchmarks use text prompts. AutoPresent/SlidesBench uses slide images to generate/condition tasks, and PPTArena uses rendered images for judging, but few benchmarks ask agents to follow a user-provided visual template, annotated screenshot, or region box.

### Gap 4: Negative and preservation constraints are weak

Many instructions include "do not change anything else" or "keep the theme." These should be scored as explicit constraints, not assumed in the reference file.

### Gap 5: There is little taxonomy of constraint types

Benchmarks rarely report performance by constraint class:

- Text content.
- Typography.
- Color.
- Alignment.
- Size/aspect ratio.
- Object identity/localization.
- Chart semantics.
- Table structure.
- Formula/value correctness.
- Cross-slide/page consistency.
- Preservation/no-extra-edit.
- Editability/native structure.

This makes it hard to diagnose what agents fail at.

### Gap 6: Multi-modal pointing and region references are missing

The user example "Make the top-right image bigger" is common in real workflows, but existing benchmarks rarely provide bounding boxes, click/drag regions, or annotated screenshots as part of the instruction.

## Recommended Benchmark Design: CUIF

The proposed benchmark could be called **CUIF: Computer-Use Instruction Following**.

### Task unit

Each task should contain:

- Initial artifact: PPTX, XLSX, DOCX, PDF, or a folder of related files.
- Optional initial desktop state if evaluating GUI CUA.
- User instruction, which may be text-only, visual-only, or mixed.
- Optional visual references: template slide/page/image, screenshot annotation, bounding box, crop, style exemplar.
- Hidden constraint specification.
- Expected output artifact.
- Optional reference artifact(s), not always single gold.

### Instruction modalities

Include at least these modes:

- Textual constraints: "Use Aptos 18 pt for all body text."
- Visual template constraints: "Make this slide match the attached template."
- Region/pointing constraints: "Make the top-right image bigger."
- Object-reference constraints: "The chart below the revenue table should use the same color palette."
- Preservation constraints: "Do not change the title or footnotes."
- Negative constraints: "Do not use red anywhere."
- Multi-turn corrections: "Undo only the chart color change."
- Ambiguous-but-resolvable constraints: "Make it more readable without changing the layout."

### Domains

Start with a balanced set:

- PowerPoint/PPTX: slides, charts, tables, images, masters, notes, animations.
- Excel/XLSX: formulas, values, formatting, charts, pivots, conditional formatting, multi-sheet consistency.
- Word/DOCX: headings, body text, tables, images, captions, comments, styles, page layout, PDF export.
- Cross-artifact tasks: create a slide from spreadsheet chart, update report from spreadsheet, export PDF and preserve layout.

### Constraint schema

A hidden task specification should use typed constraints. Example:

```json
{
  "target": {
    "artifact": "deck.pptx",
    "slide": 3,
    "object_selector": {
      "type": "image",
      "region": "top_right",
      "nearest_text": "Market share"
    }
  },
  "operation": "resize",
  "constraints": [
    {"type": "size_relative", "property": "area", "operator": ">=", "factor": 1.35},
    {"type": "aspect_ratio_preserved", "tolerance": 0.03},
    {"type": "within_canvas", "margin_px": 8},
    {"type": "no_overlap", "objects": "text"},
    {"type": "preserve", "scope": "all_other_slides"}
  ]
}
```

### Evaluation stack

Use a layered evaluator:

1. **Artifact parser**
   - PPTX: Open XML plus python-pptx for shapes/runs/tables/charts.
   - XLSX: openpyxl plus direct XML for charts/pivots/conditional formatting.
   - DOCX: python-docx plus Open XML for styles, layout, runs, tables, images.

2. **Renderer**
   - LibreOffice/headless or PowerPoint/Excel/Word where available.
   - Page/slide/chart images for layout and visual checks.

3. **Deterministic metrics**
   - Exact/approximate text.
   - Font family/size/weight/color.
   - Coordinates, sizes, alignments, margins.
   - Overlap and containment.
   - Chart types, axes, series, labels.
   - Formula/value correctness.
   - Preservation diffs.

4. **Vision/OCR metrics**
   - OCR text visibility.
   - Rendered bounding boxes.
   - Template similarity.
   - Color palette similarity.

5. **VLM judge**
   - Only for semantics/aesthetics not deterministic.
   - Binary checklist item prompts, not broad holistic ratings.

### Metrics

Report:

- Task success: all critical constraints pass.
- Constraint pass rate: passed constraints / valid constraints.
- Hard constraint pass rate: required constraints only.
- Soft quality score: weighted rubric items.
- Preservation score: unrelated object/cell/page changes avoided.
- Editability score: output remains native/editable and not rasterized when native output requested.
- Visual fidelity score: rendered output meets layout/style constraints.
- Robustness score: paraphrase/noise/multilingual/visual-reference variants.
- Turn-level and session-level scores for multi-turn tasks.

### Baselines

Include several families:

- Pure GUI CUA: screenshot/accessibility driven.
- Direct file-editing agent: Python/openpyxl/python-pptx/python-docx.
- Hybrid GUI plus file introspection.
- Structure-aware PPTX/XML agent.
- Spreadsheet code agent with execution feedback.
- Commercial/product baselines where allowed.
- Human expert baseline for calibration.

### Dataset construction

Use a mix of:

- Human-authored real office tasks.
- Edited real public templates and workbooks.
- Synthetic perturbations of real tasks, with human validation.
- Visual templates and annotated screenshots.
- Multi-turn correction traces.
- Adversarial tasks that stress preservation and negative constraints.

Collect at least two valid references for tasks with legitimate variation. For tasks where many outputs are valid, rely on constraint schema rather than full-reference matching.

## Recommended Reading List

Core CUA:

- OSWorld: [project](https://os-world.github.io/), [paper](https://arxiv.org/abs/2404.07972), [code](https://github.com/xlang-ai/OSWorld)
- WindowsAgentArena: [project](https://microsoft.github.io/WindowsAgentArena/), [paper](https://arxiv.org/abs/2409.08264), [code](https://github.com/microsoft/WindowsAgentArena)
- OSUniverse: [project](https://agentsea.github.io/osuniverse/), [paper](https://arxiv.org/abs/2505.03570)

Slides/PowerPoint:

- PPTArena: [code](https://github.com/michaelofengend/PPTArena), [paper](https://arxiv.org/abs/2512.03042)
- PPTC: [code](https://github.com/gydpku/PPTC)
- PPTC-R: [code](https://github.com/ZekaiGalaxy/PPTC-R)
- PresentBench: [project](https://presentbench.github.io/), [paper](https://arxiv.org/pdf/2603.07244), [code](https://github.com/PresentBench/PresentBench)
- AutoPresent/SlidesBench: [code](https://github.com/para-lost/AutoPresent), [paper](https://www.arxiv.org/abs/2501.00912)
- SlidesGen-Bench: [project](https://slidesgenbench.yqy314.top/), [paper](https://arxiv.org/abs/2601.09487), [code](https://github.com/YunqiaoYang/SlidesGen-Bench)
- DeckBench: [code](https://github.com/morgan-heisler/DeckBench), [paper](https://arxiv.org/abs/2602.13318)

Spreadsheets:

- SpreadsheetBench: [project/leaderboard](https://spreadsheetbench.github.io/), [code](https://github.com/RUCKBReasoning/SpreadsheetBench), [paper](https://openreview.net/forum?id=xom4egdtbB)
- SheetCopilot: [code](https://github.com/BraveGroup/SheetCopilot), [paper](http://arxiv.org/abs/2305.19308)
- InstructExcel: [code](https://github.com/microsoft/InstructExcel), [paper](https://arxiv.org/abs/2310.14495)
- SheetAgent/SheetRM: [project](https://sheetagent.github.io/), [code](https://github.com/cybisolated/SheetAgent), [paper](https://arxiv.org/abs/2403.03636)

Documents/office workflows:

- DocEdit: [code/dataset](https://github.com/adobe-research/DocEdit-Dataset)
- DocEdit-v2: [paper](https://aclanthology.org/2024.emnlp-main.867.pdf)
- OfficeBench: [code](https://github.com/zlwang-cs/OfficeBench)
- OdysseyBench: [code](https://github.com/microsoft/OdysseyBench), [paper](https://arxiv.org/abs/2508.09124)

## Practical Takeaways for Building the New Benchmark

1. Start with PowerPoint and Excel, not all office formats. Existing evaluator infrastructure is richest there, and user-facing visual constraints are common.

2. Use PPTArena as the slide-editing baseline design, but replace broad VLM scoring with more atomic deterministic constraints wherever possible.

3. Borrow PresentBench's checklist philosophy: each task should produce many binary or small-scale judgments, with grouped scores.

4. Borrow SpreadsheetBench's online-judge idea for generalization: for spreadsheet tasks, create multiple workbooks with varied values but same intended operation.

5. Borrow PPTC-R's robustness perturbations: paraphrase, noise, multilingual instructions, and API/tool changes.

6. Borrow DocEdit's localization framing: every localized edit should identify target object, operation, and bounding region or selector.

7. Explicitly score preservation. This is the most common failure mode in visual office editing and is often invisible in current benchmark summaries.

8. Keep VLM-as-judge constrained. Use it for human-like style judgments, not for checking measurable font sizes, positions, formulas, or chart series.

9. Report by constraint category. A leaderboard should show whether an agent is bad at localization, typography, chart semantics, preservation, or multi-turn correction.

10. Release trajectories and diffs. For CUA agents, task outcome is not enough; interaction traces expose whether failures are due to grounding, planning, tool limitations, or evaluation ambiguity.

## Suggested Initial CUIF Task Set

A strong first release could contain 300 tasks:

- 100 PowerPoint editing tasks.
- 80 spreadsheet manipulation/visualization tasks.
- 60 Word/document layout tasks.
- 40 cross-artifact office workflow tasks.
- 20 stress tests for multi-turn correction and robustness.

Each task should have 8 to 30 atomic constraints, with at least:

- 2 target-localization constraints.
- 2 operation/content constraints.
- 2 style/layout constraints.
- 2 preservation constraints.
- Optional semantic/aesthetic checklist items.

This would yield thousands of constraint-level labels, enough to diagnose methods meaningfully even if only 300 task shells are created.

## Local Code Inspection Appendix

Key inspected files:

- OSWorld task split: `.research/repos/OSWorld/evaluation_examples/test_all.json`
- OSWorld slide evaluator: `.research/repos/OSWorld/desktop_env/evaluators/metrics/slides.py`
- OSWorld table evaluator: `.research/repos/OSWorld/desktop_env/evaluators/metrics/table.py`
- WindowsAgentArena task split: `.research/repos/WindowsAgentArena/src/win-arena-container/client/evaluation_examples_windows/test_all.json`
- WindowsAgentArena result aggregation: `.research/repos/WindowsAgentArena/src/win-arena-container/client/show_result.py`
- OfficeBench evaluator: `.research/repos/OfficeBench/utils/evaluate.py`
- OdysseyBench evaluator: `.research/repos/OdysseyBench/evaluation/task_evaluator.py`
- OdysseyBench LLM judge: `.research/repos/OdysseyBench/llm-as-a-judge.py`
- SpreadsheetBench evaluator: `.research/repos/SpreadsheetBench/evaluation/evaluation.py`
- SpreadsheetBench parity test: `.research/repos/SpreadsheetBench/evaluation/parity_test.py`
- SheetCopilot evaluator: `.research/repos/SheetCopilot/agent/evaluation.py`
- SheetCopilot workbook comparison: `.research/repos/SheetCopilot/agent/utils/eval.py`
- SheetAgent planner/session: `.research/repos/SheetAgent/core/session.py`
- PPTC evaluator: `.research/repos/PPTC/src/evaluate.py`
- PPTC spatial checker: `.research/repos/PPTC/src/pptx_check.py`
- PPTC-R variants: `.research/repos/PPTCR/test/short/`
- PPTArena cases: `.research/repos/PPTArena/src/evaluation_pairs_refined.json`
- PPTArena judge: `.research/repos/PPTArena/src/llm/judge.py`
- PPTArena PPTX parser/diff: `.research/repos/PPTArena/src/ppt/analysis.py`
- PPTArena bulk evaluation caveat: `.research/repos/PPTArena/run_evaluation.py`
- AutoPresent page evaluator: `.research/repos/AutoPresent/evaluate/page_eval.py`
- AutoPresent reference-free judge: `.research/repos/AutoPresent/evaluate/reference_free_eval.py`
- PresentBench judge: `.research/repos/PresentBench/judge.py`
- PresentBench scoring: `.research/repos/PresentBench/scoring.py`
- SlidesGen-Bench evaluation scripts: `.research/repos/SlidesGen-Bench/eval/`
- DeckBench evaluator: `.research/repos/DeckBench/metrics/evaluator.py`
- DeckBench slide metrics: `.research/repos/DeckBench/metrics/slide_metrics.py`
- DocEdit dataset README: `.research/repos/DocEdit-Dataset/README.md`
