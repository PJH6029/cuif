# CUIF Research Direction Draft

## Working thesis

Current office-family computer-use benchmarks do not measure the most important capability needed for practical office work: **interactive production and revision of structured visual artifacts under evolving textual and visual constraints**.

CUIF should evaluate whether agents can create and edit professional PPTX/DOCX/XLSX artifacts across multiple user turns, using multimodal task inputs such as templates, screenshots, sketches, annotated references, and source files, while receiving partial credit for each requirement and turn.

The benchmark should not be framed as simply “OfficeBench but harder.” The core contribution should be an **evaluation paradigm**: multi-turn, multimodal, partial-credit office artifact evaluation with hybrid structured + rendered checks.

## Motivation

Existing office-family and computer-use benchmarks cover useful slices, but leave a gap:

- OfficeBench and OdysseyBench cover office workflows, but evaluation is mostly final-state file existence, keyword, or cell-value checks.
- SpreadsheetBench and SheetCopilot evaluate Excel well, but mostly as final workbook tasks and rarely as multimodal/multi-turn office workflows.
- PPTC/PPTC-R are multi-turn PowerPoint benchmarks, but tasks are relatively primitive/API-like and text-only.
- PPTArena improves PowerPoint visual/rubric evaluation, but is still mostly final-artifact judging and does not cover the full PPTX/DOCX/XLSX office-family setting.
- OSWorld and WindowsAgentArena include realistic GUI office tasks, but do not provide office-artifact-specific partial-credit/per-turn evaluation.
- TheAgentCompany, Mind2Web, AppWorld, and tau2 show useful partial-credit or multi-turn evaluation patterns, but are not designed for office-family artifacts.

Real office work is different from these benchmark slices:

1. Users give partial and evolving requirements.
2. Visual references matter: layout sketches, style targets, annotated screenshots, templates.
3. Agents must preserve existing artifacts while making targeted edits.
4. Office files are both structured objects and rendered visual documents.
5. Failure is rarely all-or-nothing: a slide may have correct content but wrong layout, or a spreadsheet may compute correctly but lose formatting.

## Core contribution target

CUIF should aim to contribute:

1. **Benchmark scope**
   - Practical office-family tasks over PPTX, DOCX, XLSX, and cross-file workflows.
   - Multi-turn user tasking where later turns revise, correct, or add constraints.
   - Multimodal instructions: visual templates, sketches, screenshots, style references, source figures/tables.

2. **Evaluation framework**
   - Requirement-tree partial scoring.
   - Per-turn evaluation and final evaluation.
   - Hybrid deterministic, visual, semantic, and trajectory-aware checks.
   - Explicit collateral-damage / preservation penalties.

3. **Diagnostic analysis**
   - Compare office-specific agents, general GUI agents, and code/OOXML agents.
   - Report not only final success but also content, layout, style, multimodal adherence, turn-level progress, preservation, and cost.

4. **Scalable data path**
   - Start with high-quality handmade tasks.
   - Expand through executable task templates and evaluator generation.
   - Eventually support training of an office-task-focused agent if data scale is sufficient.

## Benchmark philosophy

### Artifact-centric, not interface-exclusive

The benchmark should primarily evaluate **the produced artifact and interaction trajectory**, not mandate a single agent implementation style.

Recommended tracks:

1. **GUI-only track**
   - Agent must operate through the office application GUI.
   - Best for measuring computer-use systems directly.
   - Comparable to OSWorld/WindowsAgentArena style agents.

2. **Open-tool artifact track**
   - Agent may use GUI, code, OOXML libraries, document parsers, or hybrid tools.
   - Best for measuring the upper bound of office-task agents.
   - Lets us compare GUI-only agents against structured-text/code agents.

This avoids overcommitting to pure GUI early. If a visual-input task is hard, structured agents may still fail because they need visual grounding, but we should empirically test that instead of assuming it.

### Practicality over toy tasks

Tasks should resemble actual office work:

- make a literature-review slide from paper content and a rough sketch;
- revise a deck to follow a template while preserving content;
- create a chart from spreadsheet data and place it into a slide/document;
- modify a memo after user feedback;
- format a spreadsheet report and export/share it;
- align a figure/table according to an annotated visual instruction.

Avoid overly artificial instructions like “set title font to exactly 60 pt” unless they are part of a larger realistic request.

### Specific enough to grade, realistic enough to matter

A key design tension:

- highly ambiguous tasks are realistic but hard to evaluate reliably;
- highly specific tasks are easy to grade but can become toy benchmarks.

Recommended compromise:

- each task should have a realistic user-facing instruction;
- hidden evaluator requirements can decompose the task into concrete checks;
- visual/semantic rubrics handle open-ended portions;
- deterministic checks cover exact constraints.

## Task design axes

A useful task taxonomy is a 2x2 axis:

| Constraint type | Layout | Content |
|---|---|---|
| **Textual instruction** | “Center the figure and make the title visually dominant.” | “Summarize the paper abstract in three bullets.” |
| **Visual instruction** | “Follow this handwritten layout draft / annotated screenshot.” | “Import the correct chart/figure/table from this source image or PDF.” |

CUIF tasks should sample across all four cells.

### Example visual input types

- handwritten slide layout draft;
- screenshot with arrows or notes such as “move to here”;
- PDF/JPG template to follow;
- existing PPTX seed deck for editing;
- source chart/table/figure image;
- reference slide/document for style transfer;
- annotated document page or spreadsheet screenshot.

### Example artifact families

#### PPTX

Potential properties:

- slide count/order;
- text content and semantic summary;
- font size/family/color/bold/italic;
- shapes, images, icons, tables, charts;
- alignment, bounding boxes, z-order, spacing;
- layout fidelity to sketch/template;
- theme/master/template preservation;
- speaker notes, alt text, metadata;
- collateral damage to non-target slides.

#### DOCX

Potential properties:

- headings and paragraph structure;
- text content and semantic coverage;
- tables, images, captions;
- lists, references/citations;
- headers/footers, page breaks;
- style consistency and document layout;
- preservation of non-target sections;
- export to PDF if needed.

#### XLSX

Potential properties:

- cell values and formulas;
- named ranges and sheets;
- table formatting and conditional formatting;
- charts and pivot tables;
- filters, sorting, freeze panes, data validation;
- exact source-data preservation;
- consistency with downstream PPTX/DOCX artifacts.

## Evaluation framework

### Requirement-tree scoring

Each task should be represented as a tree or DAG of requirements:

```yaml
score:
  total: 20
  requirements:
    - id: content_correct
      points: 5
      evaluator: deterministic_text_or_llm_rubric
    - id: layout_matches_sketch
      points: 4
      evaluator: rendered_vlm_or_layout_geometry
    - id: chart_data_correct
      points: 4
      evaluator: xlsx_or_ppt_chart_data_check
    - id: turn2_revision_preserved_prior_work
      points: 3
      evaluator: per_turn_artifact_diff
    - id: no_collateral_damage
      points: 4
      evaluator: non_target_region_or_file_diff
```

Each requirement should declare:

- applicable turn;
- artifact path;
- evaluator type;
- dependencies, if any;
- points;
- failure explanation.

### Dependent vs parallel constraints

- **Parallel constraints** can receive independent points: title size, body alignment, chart color, text content.
- **Dependent constraints** should specify prerequisites: if the agent fails to import the required image, image-cropping and image-layout checks may be marked failed or not applicable depending on rubric design.

Recommended default:

- if a prerequisite is required for a downstream property, downstream points are lost;
- still report downstream checks as “blocked by prerequisite” for diagnosis.

### Turn-level evaluation

CUIF should score every user turn.

For each turn:

- run checks added by that turn;
- rerun preservation checks for previous turns;
- optionally compare against a turn-specific gold artifact;
- log which requirements became satisfied, broken, or regressed.

Avoid overcomplicating the first version with intra-turn micro-evaluation unless there is a clear trajectory requirement. Most PoC tasks can evaluate at turn boundaries.

### Evaluator types

1. **Rule-based structured checks**
   - OOXML/object extraction;
   - exact text/value/formula checks;
   - layout bounding boxes and geometry;
   - file existence/export checks;
   - chart/table/sheet metadata.

2. **Rendered visual checks**
   - render slides/pages/sheets to images;
   - compare image regions;
   - use SSIM/perceptual similarity for exact visual targets;
   - use VLM judge for sketch/template adherence.

3. **LLM/VLM-as-judge**
   - semantic text summary correctness;
   - visual content or design quality;
   - “does this chart reflect the source table?” when deterministic extraction is hard;
   - final professional quality rubric.

4. **Trajectory checks**
   - whether the agent asked for clarification when required;
   - whether the agent used/loaded required source files;
   - whether the agent avoided forbidden shortcuts in GUI-only track;
   - action count/cost/time.

## Dataset generation strategy

### Stage 1: handmade high-quality PoC

Create 2--3 tasks by hand, with gold artifacts and evaluator specs.

Goal: validate task schema, artifact rendering, partial-credit scoring, and agent smoke tests.

### Stage 2: template-driven data generation

For each seed workflow:

1. choose artifact family and task type;
2. sample `k` evaluation properties from a property bank;
3. generate source files and visual constraints;
4. apply deterministic transformations to produce gold artifacts;
5. write or synthesize natural-language multi-turn instructions;
6. derive evaluator leaves from generation metadata;
7. manually inspect a subset for quality.

### Stage 3: scale and split

Possible scale targets:

- **PoC:** 2--3 handmade tasks;
- **pilot benchmark:** 30--50 high-quality tasks;
- **paper benchmark:** 200--300 high-quality test tasks;
- **training/large-scale set:** 1,000--2,000+ tasks if generation and validation are reliable.

Hold out template families, source domains, and visual styles to prevent leakage.

## Roadmap toward August

### Late April: literature and positioning

- Finish literature review.
- Identify benchmark gap and novelty claim.
- Decide PoC scope and artifact family focus.

Status: mostly complete in `literature_review/`.

### By May 3: benchmark spec

Deliverables:

- task schema draft;
- evaluator schema draft;
- property bank for PPTX-first tasks;
- PoC task list and expected artifacts;
- decision on GUI-only vs open-tool tracks.

### Early May: PoC benchmark

Deliverables:

- 2--3 handmade tasks;
- one PPTX create task from visual sketch/template;
- one PPTX edit task from seed deck + visual/text constraints;
- optional XLSX→PPTX or DOCX/PDF→PPTX cross-file task;
- renderer and evaluator smoke tests;
- baseline agent run on at least one simple agent.

### Mid/Late May: evaluation pipeline

Deliverables:

- requirement-tree evaluator;
- structured PPTX checks;
- rendered image checks;
- LLM/VLM judge wrapper with cached outputs;
- per-turn score report;
- collateral-damage checks.

### June: dataset generation pipeline

Deliverables:

- property bank;
- seed workflow templates;
- automatic gold artifact generation;
- automatic evaluator leaf generation;
- manual review workflow;
- pilot set of 30--50 tasks.

### July: scale benchmark

Deliverables:

- 200--300 high-quality evaluation tasks if feasible;
- multimodal input packaging;
- train/dev/eval split plan;
- benchmark runner and baseline documentation.

### August: model evaluation and paper draft

Deliverables:

- evaluate office-specific, GUI, and code/OOXML agents;
- ablate visual input, per-turn memory, self-check, and interface type;
- produce diagnostic tables and qualitative failure analysis;
- write paper draft around benchmark + evaluator + agent analysis.

## Key research questions

1. Do current office/computer-use agents fail more on visual constraints, multi-turn revision, or artifact preservation?
2. Does per-turn partial credit reveal failures hidden by final-only evaluation?
3. Are GUI agents or structured-code agents better for multimodal office artifact tasks?
4. Can visual instructions such as sketches/templates be evaluated reliably enough for a benchmark?
5. Can task/evaluator generation scale without sacrificing benchmark validity?

## Expected paper story

A strong paper story:

1. Existing office benchmarks are too simple, final-only, single-turn, and text-heavy.
2. CUIF introduces a practical benchmark for multi-turn multimodal office artifact production.
3. CUIF uses requirement-tree partial credit with hybrid structured/rendered/semantic evaluation.
4. Current agents show distinct failure modes: visual grounding, preservation, revision, cross-file consistency, and layout fidelity.
5. This opens a path toward training office-task-focused computer-use agents.

## Immediate TODOs

- [ ] Finalize PoC task schema.
- [ ] Select exact 2--3 PoC tasks.
- [ ] Choose rendering stack for PPTX/DOCX/XLSX artifacts.
- [ ] Implement minimum evaluator interface.
- [ ] Build first PPTX visual-layout task.
- [ ] Build first PPTX edit-from-seed task.
- [ ] Run a smoke-test baseline.
- [ ] Decide initial benchmark track policy: GUI-only, open-tool, or both.
