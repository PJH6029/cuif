# CUIF PoC Documentation

## PoC objective

Build the smallest convincing proof-of-concept for CUIF: a mini benchmark with 2--3 office-family tasks that demonstrates **multi-turn, multimodal, partial-credit office artifact evaluation**.

The PoC should prove that CUIF is not just “harder OfficeBench.” It should show a working evaluator that can grade:

- visual task constraints;
- structured office artifact properties;
- per-turn progress;
- partial credit;
- preservation / collateral damage.

## PoC thesis

A useful PoC does not need hundreds of tasks. It needs to show that the benchmark idea is technically feasible and diagnostically valuable.

The desired PoC result:

> Given a small set of multimodal office tasks, CUIF can produce clear partial-credit reports showing which constraints an agent satisfied, missed, broke across turns, or damaged outside the target region.

## PoC scope

### Initial artifact focus

Start with **PPTX-first** tasks.

Reason:

- PowerPoint is visually rich, making multimodal constraints natural.
- PPTX has structured OOXML properties and rendered-slide appearance.
- Existing work has PPTC and PPTArena, making comparison easy.
- PPTX tasks can later incorporate XLSX/DOCX/PDF inputs.

Stretch goal: include one cross-file task, preferably XLSX→PPTX or PDF/paper→PPTX.

### In scope

- 2--3 handmade tasks.
- 2--3 user turns per task.
- Visual input such as sketch/template/screenshot.
- PPTX output artifacts.
- Requirement-tree evaluator.
- Turn-level score report.
- Structured PPTX checks.
- Rendered slide image checks.
- Optional LLM/VLM judge for semantic or visual rubric checks.

### Out of scope for PoC

- Large dataset generation.
- Full agent training.
- Human evaluation pipeline.
- Full DOCX/XLSX property coverage.
- Complex GUI automation infrastructure unless trivial to reuse.
- Intra-turn micro-trajectory scoring.

## PoC task candidates

### Task 1. PPT creation from handwritten layout draft

**Goal:** create a slide or short deck from a visual layout draft plus textual content constraints.

Inputs:

- blank or minimal PPTX template;
- handwritten or sketch-like image showing layout;
- text instruction;
- optional source text such as paper title/abstract.

Possible turns:

1. Create a one-slide paper-review summary following the sketch.
2. Revise title/body hierarchy and add a source figure.
3. Apply brand colors while preserving the layout.

Evaluated properties:

- required text present;
- title/body/figure placed in correct regions;
- visual similarity to sketch layout;
- font hierarchy;
- no unintended extra objects;
- final slide readable and visually coherent.

Evaluator types:

- PPTX text/object extraction;
- bounding-box checks;
- rendered-slide VLM or image-region check;
- optional LLM judge for semantic summary quality.

### Task 2. PPT edit from seed deck with annotated screenshot

**Goal:** revise an existing deck based on visual annotations while preserving non-target content.

Implemented PoC package:

- `poc/tasks/incident_response_annotated_deck`
- Scenario: revise a Nimbus reliability operations seed deck from an annotated slide screenshot.
- Turn 1 tests targeted layout repair on slide 2 plus preservation of non-target slides.
- Final turn tests incremental styling, caption/owner additions, turn-1 layout preservation, and collateral-damage checks.

Inputs:

- seed PPTX;
- screenshot of target slide with handwritten annotation, e.g. arrow/text saying “move this to pixel/area,” “make this chart larger,” or “align with this edge”;
- text instruction describing the intended edit.

Possible turns:

1. Move/resize a figure or chart according to annotation.
2. Change title style and add a short caption.
3. Fix spacing without changing other slides.

Evaluated properties:

- correct slide selected;
- target object changed as requested;
- non-target objects preserved;
- non-target slides preserved;
- annotation-following layout check;
- caption/text content correct.

Evaluator types:

- object matching and bounding-box geometry;
- non-target slide diff;
- rendered visual comparison;
- exact/semantic text check.

### Mixed Task. Paper PDF to review deck with annotated revision

**Goal:** combine Task 1's visual layout-following paper-review creation with Task 2's annotated screenshot revision and preservation checks.

Implemented PoC package:

- `poc/tasks/transformer_paper_review_deck`
- Scenario: create and revise a SNUPI reading-group review deck for *Attention Is All You Need* from the source paper PDF.
- Turn 1 tests PDF-to-PPTX creation, paper figure extraction/embedding, formula inclusion, and protected logistics-slide preservation.
- Turn 2 tests annotated slide-2 layout repair, enlarged Figure 1 placement, right-rail callouts, and formula/slide preservation.
- Final turn tests seminar styling, prior-turn figure/formula preservation, final critique text, and a live VLM rubric over rendered slide previews.

Inputs:

- seed seminar PPTX template;
- source paper PDF;
- extracted reference crops for paper figures/formula;
- annotated screenshot for the slide-2 layout revision;
- seminar style reference.

Evaluated properties:

- required review text present;
- embedded paper figures visually match PDF reference crops;
- attention formula appears as editable text and as a PDF-derived formula crop;
- annotated screenshot layout is followed;
- protected non-target slide is preserved;
- VLM judge verifies figure/formula visibility on rendered previews.

### Task 3. XLSX/PDF/source-data to PPT chart slide (stretch)

**Goal:** create or update a slide using external source data.

Inputs:

- XLSX with table data, or PDF/paper table;
- PPTX template;
- visual layout reference for chart placement.

Possible turns:

1. Build a chart from the specified data and place it in the slide.
2. Add a one-sentence insight below the chart.
3. Adjust chart style to match template and preserve source data.

Evaluated properties:

- correct source data used;
- chart type correct;
- chart values/labels correct;
- chart positioned according to layout reference;
- insight text semantically reflects the data;
- source XLSX unchanged if preservation required.

Evaluator types:

- XLSX value/range check;
- PPT chart data extraction if feasible;
- rendered chart VLM check;
- LLM judge for insight correctness;
- file preservation check.

## PoC evaluation schema

Each task should have a machine-readable evaluator spec.

Example:

```yaml
id: poc_ppt_sketch_001
artifacts:
  input:
    - seed.pptx
    - sketch.png
    - source.txt
  output:
    - result.pptx
turns:
  - id: turn1
    instruction: "Create the slide following the sketch."
    checks:
      - id: required_title
        evaluator: pptx_text_contains
        points: 2
      - id: layout_regions
        evaluator: pptx_bbox_regions
        points: 4
      - id: sketch_similarity
        evaluator: rendered_vlm_layout
        points: 4
  - id: turn2
    instruction: "Apply the brand style and add the source figure."
    checks:
      - id: brand_colors
        evaluator: pptx_style_check
        points: 3
      - id: figure_present
        evaluator: rendered_or_image_match
        points: 3
      - id: prior_layout_preserved
        evaluator: turn_diff_preservation
        points: 4
score:
  aggregation: weighted_sum
  total_points: 20
```

## Minimum evaluator components

### 1. Artifact loader

Responsibilities:

- locate input/output artifacts;
- validate expected files exist;
- normalize paths by task/turn;
- record metadata for score reports.

### 2. PPTX structured extractor

Minimum fields:

- slides;
- shapes;
- text runs;
- images;
- tables/charts if easy;
- bounding boxes;
- font size/color/family where accessible.

Useful libraries/tools:

- `python-pptx` for structured extraction and simple edits;
- OOXML inspection for properties not exposed by `python-pptx`;
- LibreOffice or similar renderer for slide images.

### 3. Renderer

Responsibilities:

- render PPTX to slide images;
- optionally crop regions;
- store deterministic file names for judge/cache use.

### 4. Check functions

Initial checks:

- `file_exists`;
- `pptx_text_contains`;
- `pptx_slide_count`;
- `pptx_bbox_region`;
- `pptx_font_size_relation`;
- `pptx_color_match`;
- `pptx_non_target_slide_unchanged`;
- `rendered_image_similarity`;
- `llm_text_rubric`;
- `vlm_layout_rubric`.

### 5. Score aggregator

Responsibilities:

- run checks by turn;
- compute points earned / total;
- show blocked checks if dependencies failed;
- report regressions from previous turns;
- emit JSON and markdown score reports.

## Partial-credit policy

### Default scoring

- Each check has points.
- Task score is sum of passed points divided by total points.
- Turn score is sum over checks assigned to that turn.
- Final score includes final checks plus accumulated preservation checks.

### Dependencies

If a check depends on another object existing:

- prerequisite failure should mark dependent checks as failed or blocked;
- blocked checks still count as lost points unless explicitly marked diagnostic-only;
- report should explain the dependency.

### Preservation

Every multi-turn task should include preservation checks:

- previous-turn requirements still satisfied;
- non-target slides/pages/sheets unchanged;
- source files unchanged when required;
- no unexpected extra/deleted objects.

## Baselines for PoC

Minimum:

- one LLM/code-agent baseline that can manipulate PPTX using Python libraries;
- one manual/gold run to validate evaluator behavior.

Preferred if time allows:

- a GUI agent or general computer-use baseline;
- a structured open-tool baseline;
- compare GUI-only vs open-tool track on at least one task.

The PoC does not need to prove final SOTA. It only needs to show that CUIF scoring reveals meaningful differences.

## PoC success criteria

The PoC is successful if it demonstrates all of the following:

1. **Task feasibility**
   - 2--3 tasks can be packaged with inputs, turns, expected outputs, and evaluator specs.

2. **Evaluation feasibility**
   - evaluator produces a partial-credit JSON/markdown report;
   - checks include both structured PPTX checks and rendered visual checks;
   - per-turn scores are visible.

3. **Diagnostic value**
   - at least one baseline gets partial credit rather than only pass/fail;
   - report identifies concrete failures such as wrong layout, missing content, broken preservation, or visual mismatch.

4. **Novelty signal**
   - tasks clearly include multimodal constraints;
   - tasks require multi-turn revision or preservation;
   - evaluation would not be captured by OfficeBench-style final keyword/file checks alone.

## Immediate implementation TODOs

### Spec and task design

- [ ] Define task directory structure under `poc/tasks/`.
- [ ] Define evaluator YAML/JSON schema.
- [ ] Pick final 2--3 PoC task concepts.
- [ ] Create or collect seed PPTX templates.
- [ ] Create visual inputs: sketch, annotated screenshot, template image.
- [ ] Write turn-by-turn user instructions.
- [ ] Create gold artifacts manually or via script.

### Evaluation pipeline

- [ ] Implement PPTX structured extraction.
- [ ] Implement PPTX rendering to images.
- [ ] Implement first deterministic checks.
- [ ] Implement score aggregation.
- [ ] Implement markdown/JSON result report.
- [ ] Add optional VLM/LLM judge wrapper with caching.
- [ ] Add preservation/collateral-damage checks.

### Smoke tests

- [ ] Run evaluator on gold artifact and expect near/full score.
- [ ] Run evaluator on intentionally broken artifacts and check failures are caught.
- [ ] Run at least one baseline agent or scripted solver.
- [ ] Compare final-only score vs partial/per-turn report.

### Documentation

- [ ] Document task authoring workflow.
- [ ] Document evaluator leaf types.
- [ ] Document how to add a new check.
- [ ] Record known limitations and false positives/negatives.

## Expected PoC outcome

A compelling PoC result should look like:

- a small gallery of multimodal office tasks;
- a score report that breaks down each turn and requirement;
- examples where an agent gets content right but layout wrong, or handles turn 1 but breaks it after turn 2;
- evidence that CUIF captures failures hidden by final-only evaluation;
- a concrete path from handmade tasks to generated benchmark tasks.
