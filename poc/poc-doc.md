# CUIF PoC documentation

## PoC objective

Build the smallest convincing proof-of-concept for CUIF as a benchmark for **layout/template-constrained editable office artifacts**.

The PoC should show that CUIF can grade whether an agent can turn textual and visual requirements into a correct PPTX deliverable, revise it across user turns, and avoid damaging prior work or protected regions. The point is not to prove that agents lack visual perception in the abstract. The point is to evaluate whether agents can ground visual and textual constraints into the **structured, editable objects** that real office work requires.

## PoC thesis

A useful PoC does not need hundreds of tasks. It needs to make one claim undeniable:

> Given a small set of multimodal office tasks, CUIF can produce per-turn partial-credit reports that identify content correctness, layout/template fidelity, native editability, source-data use, prior-turn regression, and collateral damage.

This is the differentiator from broad CUA benchmarks and one-shot office benchmarks. The PoC should be a diagnostic evaluator, not just a task bundle.

## What the PoC should prove

The PoC is successful if it demonstrates all of the following:

1. **Visual constraints become graded artifact requirements**
   - Examples: follow a sketch, match an annotated screenshot, place a figure in a requested region, or apply a style reference.
   - The visual input is not merely an observation; it defines a requirement that is checked in the output file.

2. **Office files are evaluated as both structure and rendering**
   - Structured checks inspect PPTX text, object names, charts, formulas, images, styles, and slide preservation.
   - Rendered checks produce slide previews for layout review, visual rubrics, and human/debug inspection.

3. **Multi-turn revision is scored at turn boundaries**
   - Each turn adds, revises, or preserves requirements.
   - Later turns are checked for regression against earlier turn requirements.

4. **Partial credit exposes failure modes**
   - A model can get content correct but fail layout.
   - It can follow layout but flatten a native chart/image incorrectly.
   - It can satisfy a new revision while damaging a protected slide.

5. **GUI and open-tool tracks can be compared on the same tasks**
   - GUI-only agents operate through the office GUI.
   - Open-tool agents may use code, OOXML libraries, renderers, file parsers, or a hybrid workflow.
   - CUIF reports action-space-specific failures rather than assuming one interface is the benchmark target.

## PoC scope

### Initial artifact focus

Start with **PPTX-first** tasks.

Reasons:

- PowerPoint is visually rich, so layout/template/style constraints are natural.
- PPTX exposes structured OOXML properties as well as rendered-slide appearance.
- Existing PowerPoint work such as PPTC/PPTC-R and PPTArena makes comparison easy.
- PPTX tasks can incorporate XLSX, PDF, DOCX, PNG/SVG, and text inputs without needing full evaluator support for every output family in the first PoC.

Stretch scope: include cross-file inputs such as XLSX-to-PPTX chart creation or PDF-to-PPTX figure extraction, but keep the evaluated output PPTX until the DOCX/XLSX evaluators mature.

### In scope

- 3 flagship PoC tasks selected from the current task packages.
- 2--3 user turns per task.
- Visual inputs: sketch, style reference, source figure, rendered screenshot, or annotated screenshot.
- PPTX output artifacts with native editable objects where applicable.
- Requirement-tree partial scoring.
- Per-turn score reports.
- Structured PPTX checks.
- Rendered slide previews and optional VLM layout/style rubrics.
- Collateral-damage and turn-regression checks.

### Out of scope for this PoC

- Claiming broad occupational coverage.
- Full training-scale data generation.
- Full human expert grading pipeline.
- Full DOCX/HWP/OFD/JTD support.
- Intra-turn mouse/keyboard micro-trajectory scoring.
- Treating multilingual/localized formats as the central paper claim.

## Flagship PoC tasks

Use the existing packages as a curated demonstration set rather than presenting every toy/smoke task as benchmark-quality.

### 1. `incident_response_annotated_deck`

**Scenario:** Revise a Nimbus reliability operations deck from an annotated screenshot.

**Why it matters:** This is the cleanest layout/template constraint example. The agent must edit only the target slide, follow spatial annotations, keep prior content, and preserve non-target slides.

**Core capability tested:** annotated visual instruction grounding plus collateral-damage-free editing.

**Key checks:**

- slide count and required text;
- metric tiles in the top row;
- incident trend panel enlarged into the requested region;
- risk callout moved to the lower-right region;
- protected slides 1, 3, and 4 preserved;
- final-turn style/caption additions do not regress turn-1 layout.

### 2. `renewable_power_briefing_deck`

**Scenario:** Create a renewable-electricity briefing deck from a source workbook and visual layout/style references.

**Why it matters:** This tests cross-file source grounding and native chart creation, not just text placement. The correct answer must preserve values, labels, chart type, and slide layout.

**Core capability tested:** XLSX/source-data fidelity plus editable PPTX chart layout.

**Key checks:**

- chart categories and series match workbook values;
- chart is a native clustered column chart, not a screenshot fallback;
- chart and title occupy expected regions;
- audit slide contains exact source values;
- protected invariant slide is preserved;
- final style/revision constraints preserve chart data.

### 3. `transformer_paper_review_deck`

**Scenario:** Build and revise a reading-group review deck for *Attention Is All You Need* from a source paper PDF, figure crops, annotated slide layout, and seminar style reference.

**Why it matters:** The semantic topic is familiar to frontier models, so the task should not be sold as a hard paper-understanding challenge. Its value is that it combines source figure extraction, formula inclusion, visual layout revision, editable text, and preservation.

**Core capability tested:** PDF/source-figure grounding plus multi-turn figure/formula/layout preservation.

**Key checks:**

- required review text and exact formula string;
- Figure 1 and attention mechanism figure visually match reference crops;
- formula appears as editable text and image crop where required;
- annotated slide-2 layout constraints are satisfied;
- protected logistics slide is preserved;
- final seminar styling does not damage prior figure/formula requirements.

### Support/smoke tasks

- `toy_pptx_layout`: keep as evaluator smoke test only.
- `launch_readiness_deck` and `aurora_paper_review_deck`: use as additional examples or dev tasks, not as the central novelty evidence unless they are strengthened with native-object, template, or cross-file constraints.

## PoC task design rules

Every flagship task should include these elements:

1. **A realistic office scenario**
   - Examples: incident review, policy briefing, research seminar, executive update.
   - Avoid single-command formatting tasks unless they are embedded in a larger workflow.

2. **At least one visual requirement**
   - Sketch, annotated screenshot, style reference, source figure, template preview, or rendered target.

3. **At least one structured artifact requirement**
   - Native chart/table/text box, editable formula/text, object name, chart data, slide master/theme, or image crop match.

4. **At least one preservation requirement**
   - Protected slide/page/sheet, source file unchanged, non-target region stable, speaker notes/metadata retained, or previous-turn layout preserved.

5. **At least two turns**
   - Turn 1 creates or repairs the artifact.
   - Final turn revises a local constraint and tests regression/preservation.

6. **Partial-credit checks**
   - Content/source correctness.
   - Layout/region correctness.
   - Style/template correctness.
   - Native editability.
   - Preservation/regression.

## Evaluation schema

The task manifest should encode requirements as a weighted DAG of checks. A simplified pattern:

```yaml
turns:
  - id: turn1
    instruction: "Create or repair the deck from source inputs and visual references."
    checks:
      - id: file_exists
        evaluator: file_exists
        points: 1
      - id: required_content
        evaluator: pptx_text_contains
        points: 4
      - id: native_chart_data
        evaluator: pptx_chart_data
        points: 5
      - id: visual_layout_region
        evaluator: pptx_bbox_region
        points: 4
      - id: protected_slide_preserved
        evaluator: pptx_preservation_diff
        points: 4
  - id: final
    instruction: "Apply a revision while preserving turn-1 work."
    checks:
      - id: revised_style
        evaluator: pptx_style_check
        points: 3
      - id: prior_layout_preserved
        evaluator: pptx_preservation_diff
        points: 3
      - id: rendered_layout_review
        evaluator: vlm_layout_rubric
        points: 0
        optional: true
        diagnostic: true
```

### Required evaluator families

1. **File and schema checks**
   - `file_exists`, slide count, output naming, artifact references.

2. **Structured PPTX checks**
   - text containment;
   - object names/selectors;
   - bounding boxes and regions;
   - font/style checks;
   - image similarity against source/reference crops;
   - chart type/data extraction;
   - formula/text presence;
   - preservation diffs for protected slides and selected objects.

3. **Rendered checks**
   - render deck to PNG previews;
   - attach previews to reports;
   - optionally run VLM layout/style rubrics with cached outputs.

4. **Turn-regression checks**
   - compare final output against turn-1 output for selected objects or regions;
   - mark requirements as satisfied, failed, blocked, or regressed.

## Report expectations

Every run report should include:

- total score and per-turn score;
- score by capability bucket: content/source, layout, style/template, native editability, preservation/regression;
- failed checks with concrete selector/region evidence;
- blocked checks when dependencies fail;
- rendered slide previews for visual debugging;
- optional LLM/VLM judge outputs with cache keys and model metadata;
- a concise natural-language summary of the agent's failure modes.

## Baseline experiment design

The PoC should be run on at least three agent/interface settings when feasible:

1. **Open-tool frontier agent**
   - May use Python, OOXML, file parsers, and renderers.
   - Expected to be strong on structured edits but still fail visual layout or preservation.

2. **GUI-only CUA agent**
   - Uses screenshot observation and mouse/keyboard actions.
   - Expected to reveal spatial manipulation cost and precision failures.

3. **Hybrid or office-specific agent**
   - Uses structured edits plus rendered self-checks.
   - Useful as an aspirational baseline and for ablations.

Useful ablations:

- remove visual input;
- remove turn history;
- disallow code/OOXML;
- disallow rendered self-check;
- require native editability instead of allowing flattened screenshots.

## Scaling path after PoC

The PoC should lead directly into a template-family generation pipeline.

1. **Human designs workflow families**
   - Example families: incident review deck, public reporting template, KPI briefing, research paper deck, grant pitch, board update.

2. **Scripts instantiate variants**
   - Vary data, labels, source documents, colors, layouts, protected regions, and turn order.

3. **Gold and evaluator leaves are generated together**
   - The same metadata that places objects in gold artifacts should generate bbox/style/chart/text checks.

4. **Visual instructions are generated from artifacts**
   - Render seed/gold slides.
   - Add arrows, callouts, region boxes, or sketch-like SVGs.

5. **Strong-agent filtering controls difficulty**
   - Keep benchmark tasks where strong agents do not saturate.
   - Reserve easy tasks for smoke/dev/train splits.

## Immediate PoC success criteria

Before claiming PoC completion, verify:

- all flagship manifests validate;
- mock runs pass deterministic checks;
- reports include per-turn partial credit and rendered previews;
- at least one task exercises each of: visual layout, native chart/data, source figure/image matching, preservation, final-turn regression;
- `toy_pptx_layout` remains a smoke task, not a flagship novelty claim;
- the documentation consistently frames CUIF as layout/template-constrained editable artifact evaluation rather than generic visual perception.
