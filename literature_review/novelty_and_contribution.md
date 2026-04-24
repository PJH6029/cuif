# CUIF novelty and contribution positioning

This note is an opinionated positioning memo for the proposed CUIF benchmark. It answers the concern: **is CUIF novel enough, or is it just a more complex office benchmark with visual inputs?**

## Short answer

A weak version of CUIF would be incremental. A strong version can be a clear contribution.

- **Weak framing:** “OfficeBench/PPTC/SheetCopilot, but harder and with some visual inputs.”
- **Strong framing:** “A benchmark and evaluation framework for interactive, multimodal, partial-credit office artifact production across PPTX/DOCX/XLSX.”

The novelty should not rest only on “visual input.” The stronger novelty is the **combination** of:

1. practical office-family artifact production;
2. multi-turn user task evolution;
3. multimodal task instructions and constraints;
4. per-turn and partial-credit evaluation;
5. structured + rendered artifact scoring;
6. collateral-damage / preservation checks;
7. scalable task/evaluator construction.

## Why “harder + visual input” alone is risky

If CUIF is presented only as a harder office benchmark, reviewers may reasonably compare it to:

- **OfficeBench / OdysseyBench:** office workflow tasks and long-horizon context;
- **PPTC / PPTC-R:** multi-turn PowerPoint task completion;
- **SpreadsheetBench / SheetCopilot:** Excel-focused task completion and rich spreadsheet properties;
- **PPTArena:** PowerPoint editing with visual/LLM judging and partial-credit rubrics;
- **OSWorld / WindowsAgentArena:** real desktop computer-use tasks including office apps;
- **TheAgentCompany:** practical professional tasks with checkpoint partial credit.

Against that landscape, “we made tasks more complex and added images” could sound incremental.

## Strong contribution thesis

CUIF should be framed as evaluating a missing capability:

> **Interactive professional office artifact production under textual and visual constraints.**

A stronger paper-level claim:

> Existing office benchmarks mainly evaluate final-state success on simple or one-shot tasks. CUIF evaluates whether agents can iteratively create and revise professional PPTX/DOCX/XLSX artifacts under multimodal constraints, with fine-grained partial credit over artifact structure, rendered appearance, per-turn progress, and preservation of non-target content.

This makes CUIF more than a task collection. It becomes an evaluation paradigm for office-family computer-use agents.

## Core novelty pillars

### 1. Multimodal instructions as constraints, not just observations

Many computer-use benchmarks let agents observe screenshots. CUIF should emphasize that **the task instruction itself can be multimodal**:

- a handwritten slide layout draft;
- a screenshot with annotations;
- a reference deck/style target;
- an image of a desired table/chart layout;
- a marked-up document page;
- a visual brand/template constraint.

This is different from simply giving an agent a GUI screenshot. The visual input defines requirements that must be grounded into the final artifact.

### 2. Multi-turn office task evolution

Real office work is iterative. Users revise requirements, add constraints, correct mistakes, and ask for preservation. CUIF should model turns such as:

1. create an initial artifact from source data;
2. revise layout according to a sketch;
3. change style while preserving data and template;
4. add an explanation or export/share artifact;
5. correct a specific issue without disturbing prior work.

This differentiates CUIF from one-shot editing benchmarks.

### 3. Per-turn and partial-credit evaluation

The strongest contribution is not simply final grading. CUIF should save and score expected states or requirements after each user turn.

Example turn-level requirements:

- after turn 1: chart uses correct source cells;
- after turn 2: chart layout matches visual sketch;
- after turn 3: brand colors applied while chart data and non-target slides are preserved;
- final: exported document/deck/spreadsheet satisfies all accumulated constraints.

This supports diagnosis of where agents fail: initial grounding, revision, preservation, visual alignment, or final polish.

### 4. Requirement-tree scoring

A CUIF task should not be one binary check. It should be a weighted tree of requirements:

```text
Task score
├── content/data correctness
│   ├── required text present
│   ├── spreadsheet formula/value correct
│   └── chart data source correct
├── layout/style fidelity
│   ├── bounding boxes/alignment
│   ├── fonts/colors/themes
│   └── rendered visual quality
├── multimodal constraint adherence
│   ├── sketch followed
│   ├── reference style matched
│   └── annotated constraints satisfied
├── turn-level progress
│   ├── turn 1 requirements
│   ├── turn 2 requirements
│   └── turn 3 requirements
└── preservation/collateral damage
    ├── source file unchanged
    ├── non-target slides/pages/sheets unchanged
    └── no unintended deletions or style drift
```

This is a clearer contribution than simply adding more tasks.

### 5. Structured + rendered artifact evaluation

Office artifacts are both structured files and visual documents. CUIF should exploit both views:

- **Structured checks:** OOXML/object tree, text runs, tables, formulas, charts, styles, slide masters, named ranges, headers/footers.
- **Rendered checks:** screenshots of slides/pages/sheets, layout similarity, VLM judgments, image crops, visual reference matching.

This hybrid approach is important because XML checks miss visual quality, while VLM-only checks miss exact formulas, metadata, and hidden collateral damage.

### 6. Cross-family office workflows

If feasible, CUIF should go beyond one file type:

- XLSX → PPTX: make a chart from spreadsheet data and place it in a deck;
- DOCX → PPTX: summarize a report into slides;
- XLSX → DOCX: generate a memo with tables and computed values;
- PPTX/DOCX/XLSX → PDF/export/email: produce deliverables from multiple files.

This separates CUIF from PPT-only or spreadsheet-only benchmarks.

### 7. Scalable generation with executable evaluators

A benchmark contribution becomes stronger if CUIF includes a scalable construction method:

- start from parameterized seed workflows;
- generate source artifacts and gold intermediate/final states by executable scripts;
- render visual constraints from artifacts or annotations;
- derive evaluator leaves from generation metadata;
- create train/dev/test variants with held-out templates/task families.

This would support future training of office-task agents, not only evaluation.

## Suggested paper contribution bullets

A CUIF paper could claim contributions like:

1. **Benchmark:** a practical office-family benchmark covering PPTX/DOCX/XLSX and cross-file workflows with multi-turn, multimodal task instructions.
2. **Evaluation framework:** a hybrid evaluator that combines deterministic artifact checks, rendered visual checks, LLM/VLM semantic rubrics, per-turn states, and collateral-damage penalties.
3. **Partial-credit diagnostics:** a requirement-tree scoring scheme that reports not only success rate but also content, layout, multimodal adherence, preservation, per-turn progress, and trajectory-related failures.
4. **Dataset construction method:** a scalable pipeline for generating office tasks, multimodal constraints, gold artifacts, and evaluator leaves from executable workflow templates.
5. **Agent analysis:** a benchmark study showing that existing office-specific and general computer-use agents fail in different ways on visual constraints, revision, preservation, and cross-artifact reasoning.

## Recommended positioning against related work

| Related work family | What they already cover | CUIF differentiation |
|---|---|---|
| OfficeBench / OdysseyBench | Cross-app office workflows, long-horizon context | richer PPTX/DOCX/XLSX artifact scoring, multimodal constraints, partial/per-turn evaluation |
| PPTC / PPTC-R | Multi-turn PowerPoint API tasks | practical tasks, visual instructions, richer rubric, cross-family artifacts, less primitive API framing |
| SpreadsheetBench / SheetCopilot | Excel formulas/operations and some rich spreadsheet properties | multi-turn multimodal workflows and cross-file office artifact production |
| PPTArena | PowerPoint visual/rubric evaluation | broader office-family scope, multi-turn task evolution, cross-artifact workflows, trajectory/per-turn scoring |
| OSWorld / WindowsAgentArena | Real GUI computer-use with office tasks | artifact-specific partial-credit evaluator and multimodal task constraints, not only final desktop state |
| TheAgentCompany | Workplace checkpoint partial credit | office-artifact-specialized benchmark with structured/rendered PPTX/DOCX/XLSX evaluators |
| Mind2Web / VisualWebArena / AppWorld / tau2 | trajectory, multimodal, unit-test, or multi-turn patterns | adaptation of these evaluation ideas to office artifacts and professional document production |

## Minimum viable novelty target

If implementation time is limited, prioritize these features to preserve novelty:

1. **At least two artifact families** among PPTX/DOCX/XLSX, ideally including PPTX and XLSX.
2. **True multi-turn tasks** where later turns revise or constrain earlier outputs.
3. **At least one visual instruction type** beyond ordinary screenshots, such as sketches or annotated references.
4. **Requirement-tree partial scoring** with per-turn score and collateral-damage checks.
5. **Hybrid structured + rendered evaluation** rather than VLM-only or exact-file-only evaluation.

A smaller benchmark with these properties is more novel than a larger benchmark that only has harder one-shot tasks.

## Reviewer concern and response

**Concern:** “Is this just a harder version of existing office benchmarks?”

**Response:** No, if CUIF is designed around evaluation dimensions that existing office benchmarks largely omit: user-driven multi-turn revision, multimodal requirement grounding, partial-credit requirement trees, collateral-damage preservation, and hybrid structured/rendered artifact checks across office file families. The contribution is not task difficulty alone; it is a diagnostic evaluation framework for practical office artifact production.

## Bottom line

CUIF has enough novelty if it avoids being merely “complex OfficeBench.” The benchmark should be positioned as the first serious attempt to evaluate **interactive, multimodal, partially graded office artifact production** across structured office files.

The core research story should be:

> Office work is not just clicking buttons or satisfying one final string check. It is iterative production of structured visual artifacts under evolving textual and visual constraints. CUIF measures that capability directly.
