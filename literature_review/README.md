# Literature review: computer-use instruction following for office-family tasks

Date: 2026-04-24  
Scope: benchmarks, evaluation pipelines, agents, and data sources for practical office-family computer-use instruction following, with emphasis on PPTX/DOCX/XLSX tasks, multi-turn interaction, multimodal instructions, and partial-credit trajectory evaluation.

## Executive takeaways

1. **Most office-family benchmarks are still final-artifact benchmarks.** OfficeBench/OdysseyBench, SpreadsheetBench, SheetCopilot, PPTC/PPTC-R, and OSWorld/WindowsAgentArena office tasks mostly grade the final file/app state with rule-based scripts. They rarely inspect the full agent trajectory except for logs/costs.
2. **Office evaluation is fragmented by file type.** Excel benchmarks have the richest deterministic checks (cell values, formulas via recalculation, charts/pivots/styles in SheetCopilot/OSWorld), PowerPoint benchmarks increasingly use multimodal judges (PPTArena, PPTEval), and Word/PDF/email tasks are often keyword/exact-match based.
3. **The strongest recent PowerPoint direction is rubric + visual/structural judging.** PPTArena variants move beyond exact PPTX comparison: one code-audited PPTArena uses structural JSON diffs plus rendered slide images with VLM/LLM 0--5 scores; the ICLR 2026 PPTArena submission explicitly argues for tree-structured rubrics with partial credit and VLM/LLM checks.
4. **The strongest recent office-workflow direction is long-horizon context.** OdysseyBench extends OfficeBench to 300 OfficeBench-derived and 302 synthetic long-horizon office workflow tasks with chat histories/RAG settings, but its task-completion evaluator is still OfficeBench-style final-state rule checks.
5. **Partial credit exists mostly outside pure office benchmarks.** TheAgentCompany has checkpoint-weighted scoring, AppWorld has unit-test pass percentages, Mind2Web has per-step element/action/step accuracy, and tau-bench/tau2 exposes action/communication/environment components. These are directly useful design patterns for CUIF.
6. **Multi-turn user interaction is uncommon in office-family artifact benchmarks.** PPTC/PPTC-R are multi-turn PowerPoint benchmarks, and OdysseyBench includes long-horizon chat histories. General agent benchmarks such as tau2, WorkArena++, TheAgentCompany, Mind2Web, and AndroidWorld provide better multi-turn/compositional evaluation patterns, but they are not office-artifact-focused.
7. **There is no mature open benchmark that jointly satisfies all target properties**: practical PPTX/DOCX/XLSX tasks, complex multi-turn user instructions, multimodal constraints/templates/drafts, large task count, automated partial credit, and trajectory/per-turn grading. This is a credible research gap for this repo.

## What CUIF should claim as the research gap

Current office-family benchmarks under-test the behavior that makes office work hard in practice:

- **Task realism:** many tasks are atomic edits, not office workflows such as creating an investor update from a spreadsheet, modifying a branded deck under constraints, or revising a document after feedback.
- **Complexity:** many tasks can be solved by one or two primitive operations; they do not require long-horizon planning, constraint management, cross-document reasoning, or visual/layout tradeoffs.
- **Interaction:** most tasks are single-shot; even multi-step GUI trajectories are usually driven by one initial instruction rather than a user who clarifies, changes requirements, or provides turn-specific constraints.
- **Evaluation:** binary final success hides partial progress, over-editing, wrong intermediate choices, and per-turn recoverability.
- **Modality:** task instructions are mostly text; visual inputs such as templates, screenshots, rough layout sketches, annotated slides, or handwritten drafts are underused.
- **Scale:** rich office-artifact tasks are expensive to write and grade, so many benchmarks are either small or evaluate a narrow subskill.

The proposed benchmark should aim for **practical, complex, multi-turn, multimodal, large-enough office-family tasks** with **partial-credit/per-turn evaluation** over PPTX/DOCX/XLSX artifacts and, where possible, the agent trajectory.

## Recommended benchmark design principles

### 1. Hybrid grading, not one evaluator

Use multiple layers, because no single evaluator handles office artifacts well:

- **Deterministic file-state checks:** values/formulas, object presence, names, slide/document counts, metadata, exact required text, table dimensions, chart data references.
- **Tolerance-aware layout/style checks:** bounding boxes, font/style equality or ranges, alignment, color palettes, placeholder/template preservation.
- **Rendered visual checks:** slide/page/sheet screenshots with VLM and image similarity for constraints that are hard to express in XML.
- **Semantic LLM/VLM rubrics:** open-ended content quality, aesthetics, appropriateness of visual design, adherence to handwritten/visual constraints.
- **Trajectory/per-turn checks:** expected intermediate artifacts, required user-question handling, forbidden actions, over-edit penalties, and recovery from new constraints.

### 2. Score as a weighted requirement tree

A good target schema is a tree or DAG of requirements:

- top-level task score = weighted sum/product of subgoals;
- each user turn can add, revise, or remove requirements;
- each leaf names the evaluator type: deterministic, VLM, LLM, image similarity, file diff, action/trajectory event;
- penalties explicitly cover collateral damage and unnecessary edits;
- final report includes natural-language feedback and machine-readable failures.

This borrows from TheAgentCompany checkpoints, AppWorld unit-test pass counts, Mind2Web step metrics, and the newer PPTArena rubric direction.

### 3. Cover properties by artifact family

| Family | Properties to evaluate |
|---|---|
| PPTX | slide count/order, placeholders/templates, text, typography, shapes, images, charts, tables, SmartArt/diagrams, animations/transitions, speaker notes, slide master/theme, alignment/z-order, visual consistency, accessibility/alt text |
| DOCX | text content, headings/styles, tables, images, lists, references/citations, comments/track-change-like revision instructions, headers/footers, page breaks, layout fidelity, grammar/semantic quality |
| XLSX | cell values, formulas, named ranges, formatting, filters/sorts, pivot tables, charts, data validation, sheets, frozen panes, conditional formatting, formulas recalculated correctly, no collateral changes |
| Cross-file | consistency between spreadsheet data and deck/document, exported PDFs, emails/messages, citations to source files, preservation of source files, file naming/location |

### 4. Include multimodal instruction channels

The benchmark should include tasks whose instructions reference:

- a visual PPTX/DOCX/XLSX template;
- screenshots or rendered pages/slides;
- rough/handwritten layout drafts;
- annotated images (“make this table look like this,” “align chart as sketched”);
- example decks/documents used as style targets;
- visual observations in the agent loop.

### 5. Separate capabilities in reporting

Report global score but also a capability dashboard:

- final artifact success;
- per-turn success;
- partial-credit score;
- collateral damage / preservation score;
- trajectory efficiency and recoverability;
- multimodal instruction adherence;
- file-type/property coverage.

## Report map

- [`office_family_benchmarks.md`](office_family_benchmarks.md): code-level evaluation pipelines and property coverage for office-family benchmarks.
- [`agents_and_training_data.md`](agents_and_training_data.md): office-task agents, benchmark usage, methods, and datasets for training/scaling.
- [`partial_multiturn_multimodal_eval.md`](partial_multiturn_multimodal_eval.md): partial credit, trajectory scoring, multi-turn, and multimodal evaluation patterns from broader agent benchmarks.
- [`repo_audit_sources.md`](repo_audit_sources.md): audited repositories, commit hashes, important code paths, and source links.

## Primary sources used

This review uses paper/project pages plus code audits of cloned repositories. Key public sources include [OfficeBench](https://github.com/zlwang-cs/OfficeBench), [SpreadsheetBench](https://github.com/RUCKBReasoning/SpreadsheetBench), [SheetCopilot](https://github.com/BraveGroup/SheetCopilot), [PPTC](https://github.com/gydpku/PPTC), [PPTC-R](https://github.com/ZekaiGalaxy/PPTCR), [PPTAgent/DeepPresenter](https://github.com/icip-cas/PPTAgent), [PPTArena/PPTPilot](https://github.com/michaelofengend/PPTArena), [OdysseyBench](https://github.com/microsoft/OdysseyBench), [OSWorld](https://github.com/xlang-ai/OSWorld), [WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena), [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany), [Mind2Web](https://github.com/OSU-NLP-Group/Mind2Web), [VisualWebArena](https://github.com/web-arena-x/visualwebarena), [AppWorld](https://github.com/stonybrooknlp/appworld), [tau2-bench / tau3-bench](https://github.com/sierra-research/tau2-bench), and [AndroidWorld](https://github.com/google-research/android_world).
