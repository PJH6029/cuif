# CUIF research direction draft

## Working title

**CUIF: Evaluating multimodal constraint following for editable office artifacts**

Alternative title if the paper should sound narrower and sharper:

**TemplateBench-Office: Per-turn partial-credit evaluation for layout-constrained office agents**

## Updated thesis

CUIF should be motivated around artifact constraint following rather than visual perception in isolation. GUI-only computer-use agents and open-tool/code agents can both consume visual inputs. The sharper research question is:

> Can agents convert evolving textual and visual requirements into correct, editable PPTX/DOCX/XLSX artifacts while preserving templates, source data, prior-turn work, and non-target content?

CUIF evaluates **visual/textual constraint grounding into structured office artifacts**, not visual perception in isolation.

The benchmark should focus on:

- layout and template following;
- native editable object creation and editing;
- source-data and source-figure fidelity;
- multi-turn revision and regression tracking;
- preservation/collateral-damage detection;
- comparison of GUI-only and open-tool action spaces.

## Motivation

Real office work is iterative document production under constraints. A user rarely asks only for a single primitive edit such as changing a font size. More often, they provide a partially specified goal, a source file, a company or government template, a visual example, a marked-up screenshot, and then follow up with revisions.

Existing benchmarks cover important slices but leave a gap:

- Broad CUA benchmarks are strong on environment coverage and GUI action, but not on high-resolution office artifact scoring.
- Real-work benchmarks are strong on economic realism, but their grading is often expensive or coarse and not designed to isolate layout/template/preservation failures.
- Office workflow benchmarks are strong on cross-app planning and long-horizon context, but often use final-state rule checks rather than detailed artifact fidelity checks.
- PowerPoint and spreadsheet benchmarks cover individual file families, but do not jointly emphasize multi-turn visual constraints, editable-object fidelity, cross-file consistency, and preservation.

The missing capability is **interactive production of structured visual artifacts under evolving multimodal constraints**.

## Positioning against related work

See [`literature_review/layout_constraint_positioning.md`](../literature_review/layout_constraint_positioning.md) for the updated positioning memo. The high-level map is:

| Related work | Why it is strong | CUIF differentiation |
|---|---|---|
| [CUA-World / Gym-Anything](https://arxiv.org/abs/2604.06126) | Very broad software coverage and long-horizon tasks | CUIF is narrower but deeper on office artifact structure, layout/template fidelity, and per-turn deliverable diagnostics |
| [GDPval](https://arxiv.org/abs/2510.04374) | Expert-authored economically valuable deliverables across occupations | CUIF targets automated, fine-grained office artifact constraints rather than broad expert preference over final deliverables |
| [UI-Vision](https://arxiv.org/abs/2503.15661) | Desktop GUI perception/action annotations across many apps | CUIF evaluates produced editable artifacts and visual requirements, not generic GUI element grounding |
| [OfficeBench](https://arxiv.org/abs/2407.19056) / [OdysseyBench](https://arxiv.org/abs/2508.09124) | Office workflows, app switching, and long-horizon context | CUIF adds deeper PPTX/DOCX/XLSX artifact scoring, multimodal template constraints, and per-turn partial credit |
| [PPTArena](https://arxiv.org/abs/2512.03042) | Strong PPTX in-place editing with structural/rendered judging | CUIF adds multi-turn evolution, cross-file/family workflows, explicit preservation/regression scoring, and GUI-vs-open-tool comparisons |
| [SpreadsheetBench](https://arxiv.org/abs/2406.14991) | Real-world spreadsheet manipulation and value-centric XLSX checks | CUIF connects spreadsheet data to visual deliverables and evaluates layout/style/template preservation |
| [PPTC-R](https://arxiv.org/abs/2403.03788) | Robustness for PowerPoint task completion including multilingual and multi-turn stress | CUIF should use practical artifact workflows rather than primitive API-like operations |
| [ParseBench](https://arxiv.org/abs/2604.08538) | Enterprise document parsing dimensions including tables/charts/semantic formatting | CUIF is about creating and revising editable artifacts, not only parsing them |

## Core contribution target

A CUIF paper should claim four tightly connected contributions.

### 1. Benchmark scope: layout/template-constrained office artifacts

Tasks cover practical PPTX/DOCX/XLSX and cross-file workflows where the output must satisfy both user-facing visual quality and machine-checkable artifact structure.

Representative tasks:

- edit a deck slide according to an annotated screenshot while preserving all non-target slides;
- build a native PPTX chart from XLSX data and place it according to a layout reference;
- extract a figure/table from a PDF or DOCX and embed it in a slide without flattening unrelated content;
- apply a public-institution or company report template across multiple turns;
- revise a memo/deck/spreadsheet after user feedback without regressing earlier constraints.

### 2. Evaluation framework: per-turn requirement trees

CUIF grades tasks as a weighted tree/DAG of requirements. Each requirement is attached to a turn, an artifact, an evaluator, dependencies, and points.

Capability buckets:

- **Content/source fidelity:** required text, summaries, figures, formulas, source data values.
- **Layout fidelity:** bounding boxes, alignment, spacing, regions, visual hierarchy.
- **Template/style fidelity:** fonts, colors, themes, masters, headings, captions.
- **Native editability:** charts/tables/text boxes/formulas remain editable where required.
- **Multimodal grounding:** sketches, screenshots, annotations, and style references are followed.
- **Preservation:** non-target slides/pages/sheets, source files, notes, metadata, and previous-turn work remain intact.
- **Turn regression:** requirements satisfied in earlier turns are retained unless explicitly superseded.

### 3. Hybrid structured + rendered artifact checks

Office files are both structured data and visual documents. CUIF should use both views:

- **Structured checks:** OOXML/object tree, text runs, tables, formulas, charts, image hashes/similarity, style properties, slide masters/themes, named ranges, headers/footers.
- **Rendered checks:** slide/page/sheet screenshots, region comparisons, image similarity, visual layout rubrics, VLM checks.
- **Semantic checks:** LLM/VLM rubrics for open-ended summaries, visual design quality, or explanation correctness when deterministic checks are insufficient.

The key is not to replace deterministic checks with VLM judges. The strongest evaluator combines exact checks for what can be exact and visual/semantic checks for what cannot.

### 4. Action-space analysis: GUI-only vs open-tool agents

CUIF should evaluate the same tasks under different action constraints.

- **GUI-only track:** screenshot observation plus mouse/keyboard actions. This reflects classic desktop CUA constraints and tests spatial manipulation, GUI discovery, and interaction efficiency.
- **Open-tool artifact track:** code, OOXML, file parsers, renderers, and GUI tools are allowed. This measures the upper bound for office artifact agents and exposes structured-editing strengths/failures.
- **Hybrid analysis:** many strong agents will use code for precise edits and rendered previews for visual self-checking. CUIF should make that visible rather than forcing a false choice.

This reframes the original visual-perception concern: the comparison is not visual vs non-visual; it is how different action spaces satisfy the same artifact constraints.

## Task design taxonomy

### Constraint source

| Source | Examples | What it tests |
|---|---|---|
| Textual instruction | exact content, requested revision, protected text, brand rule | instruction following and turn-state tracking |
| Visual sketch/template | rough layout, style reference, target screenshot | layout/template grounding |
| Source files | XLSX data, PDF figure, DOCX report, CSV/JSON notes | source fidelity and cross-file reasoning |
| Existing artifact | seed deck, protected slides, prior turn output | preservation and collateral-damage avoidance |
| User follow-up | move only one callout, change title style, keep chart data | multi-turn revision and regression control |

### Requirement type

| Type | Examples |
|---|---|
| Content | required strings, summary bullets, captions, citations, source lines |
| Data | formula values, chart series, table rows, source workbook consistency |
| Layout | object regions, alignment, spacing, z-order, slide/page geometry |
| Style/template | font, color, theme, master layout, government/company form rules |
| Native object | editable chart, editable text, real table, preserved formula, not flattened image |
| Preservation | protected slide, non-target section, speaker notes, metadata, source file unchanged |
| Export/cross-file | PDF export, XLSX-to-PPTX consistency, DOCX-to-PPTX figure/table transfer |

## Initial benchmark scope

### PoC

Use PPTX-first tasks because they best expose layout/template issues and the current evaluator already supports structured PPTX checks.

Flagship tasks:

1. `incident_response_annotated_deck` — annotated screenshot editing plus protected-slide preservation.
2. `renewable_power_briefing_deck` — XLSX/source-data to native PPTX chart plus layout/style checks.
3. `transformer_paper_review_deck` — PDF/source-figure grounding, formula inclusion, annotated layout revision, and seminar style preservation.

Smoke/dev tasks:

- `toy_pptx_layout` for evaluator smoke testing.
- `launch_readiness_deck` and `aurora_paper_review_deck` as additional development tasks unless strengthened.

### Pilot benchmark

Target 30--50 curated tasks from 5--8 template families.

A good pilot mix:

- 40% PPTX layout/template/editing tasks;
- 25% XLSX-to-PPTX or XLSX-native chart/table tasks;
- 20% DOCX/DOCX-to-PPTX report or memo tasks;
- 15% cross-file/export/preservation tasks.

### Paper benchmark

Target 200--300 evaluation tasks if template-family generation works reliably. Hold out entire template families, visual styles, source domains, and layout generators for test splits.

## Scalable data generation strategy

The scaling problem should not be solved by writing every task by hand. The key is to move human effort to **template-family design**.

### Stage 1: human-authored template families

A human defines a workflow family:

- scenario and user goal;
- seed artifact structure;
- protected regions and invariants;
- allowed transformations;
- visual instruction types;
- scoring leaves and weights;
- difficulty knobs.

Example families:

- incident response deck repair;
- renewable-energy briefing from workbook;
- research paper review deck;
- public-sector report template;
- board KPI update;
- grant pitch one-pager;
- formatted memo with tables and figures.

### Stage 2: executable instantiation

For each family, scripts sample:

- data values and labels;
- layout variants;
- colors, fonts, and style references;
- source figures/tables;
- protected regions;
- turn order and revision type;
- distractor content.

The same scripts generate:

- seed artifacts;
- visual inputs such as sketches, screenshots, and annotation overlays;
- gold artifacts for each turn;
- evaluator leaves with selectors, regions, expected values, and dependencies.

### Stage 3: baseline filtering

Run strong agents and filter instances:

- too easy: solved with high partial score by all frontier baselines;
- too brittle: failed due to evaluator ambiguity rather than agent capability;
- useful: differentiates GUI-only, open-tool, and hybrid agents across capability buckets.

### Stage 4: sampled human review

Review every template family and a sampled subset of instances. Hidden-test families should receive stronger human inspection. This avoids needing full manual annotation for every generated instance.

## Evaluation design

### Score representation

Each task should produce:

- total score;
- per-turn score;
- per-bucket score;
- list of satisfied, failed, blocked, and regressed requirements;
- artifact previews;
- structured JSON report;
- concise human-readable report.

### Dependency policy

If a prerequisite fails, downstream checks should usually be marked failed or blocked according to the manifest:

- If the chart is missing, chart layout checks are blocked.
- If the source figure is wrong, crop/placement checks may fail or be blocked.
- If the file is missing, all artifact checks are blocked.

Blocked checks should still appear in reports to show what could not be evaluated.

### Preservation policy

Preservation should be a first-class score component, not an optional penalty.

Examples:

- protected slide exact text unchanged;
- non-target object bounding boxes within tolerance;
- source workbook unchanged;
- prior-turn chart data preserved;
- notes/metadata retained when specified;
- no flattening of editable objects unless allowed.

## Experiments

### Baselines

Evaluate at least these settings:

1. **Frontier open-tool agent**
   - Full access to Python, OOXML, parsers, renderers, and file system.

2. **GUI-only CUA agent**
   - Must use office application GUI through screenshot and mouse/keyboard actions.

3. **Hybrid office agent**
   - Structured edits plus rendered self-checks and optional GUI actions.

4. **Specialized office/PPTX agent if available**
   - Useful for comparing against general-purpose agents.

### Ablations

- No visual instruction input.
- No turn history.
- No rendered self-check.
- No code/OOXML access.
- Allow flattened screenshot outputs vs require native editability.
- Remove preservation checks from prompt/scaffold to see over-editing.

### Metrics

Report:

- final binary success if needed for comparability;
- total partial-credit score;
- per-turn score;
- content/source score;
- layout/template score;
- native editability score;
- preservation/regression score;
- cost/time/action count;
- failure taxonomy by capability and action space.

## Localized artifact direction

Localized office artifacts are promising but should not be the main paper pivot unless tooling becomes reliable.

A weak version would be "multilingual office tasks." A stronger future direction is **jurisdiction-localized document compliance**:

- Korean HWP/HWPX public-sector forms and report templates;
- Chinese OFD-style fixed-layout administrative or financial documents;
- Japanese Ichitaro/JTD-style business/administrative templates;
- locale-specific date/number/address conventions, typography, stamps/seals, tables, and boilerplate.

This direction is practical and underexplored, but risky for the current CUIF core because parsers, renderers, licensing, public templates, and evaluator support are much harder than PPTX/DOCX/XLSX. Treat it as an appendix split or follow-up benchmark unless a reliable toolchain is available.

## Risks and mitigations

### Risk 1: The benchmark looks too narrow

**Mitigation:** Frame it as narrow but deep. CUA-World covers breadth; CUIF covers high-resolution office artifact fidelity. Include cross-file tasks and at least two artifact families in the pilot.

### Risk 2: Frontier agents already solve synthetic tasks

**Mitigation:** Increase difficulty through native editability, preservation, source-data consistency, adversarial distractors, held-out templates, and baseline filtering. Avoid claiming that familiar semantic topics such as Transformer paper review are hard because of content understanding.

### Risk 3: VLM judges are unreliable

**Mitigation:** Use VLMs only where deterministic checks are insufficient. Keep structured checks as the backbone and cache all judge calls. Report judge agreement on a sampled human-reviewed subset.

### Risk 4: Task generation creates template leakage

**Mitigation:** Hold out template families, layout generators, source domains, style palettes, and instruction paraphrase families.

### Risk 5: GUI-only evaluation becomes too expensive

**Mitigation:** Keep GUI-only as one track. The primary artifact evaluator is interface-agnostic, so open-tool and hybrid tracks can still be evaluated at scale.

## Expected paper story

A strong paper narrative:

1. Real office work is iterative production of editable visual artifacts under evolving textual and visual constraints.
2. Existing benchmarks are strong on broad CUA coverage, real-work deliverables, office workflows, PPTX editing, or spreadsheet manipulation, but do not jointly provide fine-grained per-turn evaluation of layout/template-constrained office artifacts.
3. CUIF introduces a benchmark schema and evaluator for multimodal office constraints, native editability, structured/rendered checks, and preservation/regression scoring.
4. Experiments compare GUI-only, open-tool, and hybrid agents on the same tasks, showing distinct failure modes.
5. A template-family generation pipeline provides a credible path from high-quality PoC tasks to a larger benchmark and training data.

## Immediate TODOs

- [ ] Keep `poc/tasks/incident_response_annotated_deck`, `renewable_power_briefing_deck`, and `transformer_paper_review_deck` as flagship PoC tasks.
- [ ] Ensure each flagship task has clear capability buckets in the report.
- [ ] Validate all flagship manifests and mock runs.
- [ ] Add explicit native-editability requirements where missing.
- [ ] Strengthen preservation checks for non-target objects, notes, metadata, or source files.
- [ ] Run at least one open-tool frontier baseline and one GUI-style baseline if available.
- [ ] Build one template-family generator that creates seed/gold/visual-input/evaluator metadata together.
- [ ] Decide whether the pilot benchmark includes DOCX outputs or keeps DOCX as source-only context.
