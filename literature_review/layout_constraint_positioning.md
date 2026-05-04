# Layout/template constraint positioning for CUIF

This memo defines the CUIF positioning around layout/template-constrained editable office artifacts. GUI-only computer-use agents and open-tool/code agents can both consume visual inputs; the important benchmark distinction is the **action interface** and whether the agent can convert visual/textual constraints into a correct, editable office artifact.

## Updated core claim

CUIF should be positioned as a benchmark for **multimodal constraint following in editable office artifacts**, especially layout/template/style constraints that must survive multi-turn revision.

A concise thesis:

> Real office work is not only GUI navigation or one-shot deliverable generation. It is iterative production of editable PPTX/DOCX/XLSX artifacts under evolving textual and visual constraints: templates, layout sketches, annotated screenshots, brand rules, source tables, and preservation requirements. CUIF evaluates those constraints with per-turn partial credit using both structured artifact checks and rendered visual checks.

This changes the motivation from **"agents lack visual perception"** to **"agents struggle to ground visual and textual requirements into structured, editable, preservation-safe office artifacts."**

## Why CUIF should not compete on broad coverage alone

Recent benchmarks are already very strong on scale, occupational realism, or GUI coverage:

- [Gym-Anything / CUA-World](https://arxiv.org/abs/2604.06126) scales environment creation to 200 software applications and over 10K long-horizon tasks, with CUA-World-Long often requiring over 500 steps. CUIF should not try to beat this on application breadth or trajectory length.
- [GDPval](https://arxiv.org/abs/2510.04374) anchors benchmark value in economic realism: 44 occupations across top GDP sectors, tasks constructed from expert work products, and a 220-task gold subset with automated grading service. CUIF should not try to beat this on broad real-world occupational coverage.
- [UI-Vision](https://arxiv.org/abs/2503.15661) directly targets desktop GUI perception/action with dense demonstrations, bounding boxes, UI labels, and action trajectories across 83 applications. CUIF should not frame itself as another generic GUI perception benchmark.

CUIF can still be valuable if it is **narrower but deeper**: high-resolution evaluation of layout/template-constrained office artifacts and the tradeoff between GUI actions and structured open-tool actions.

## Competitor map and CUIF differentiation

| Related work | Existing strength | Gap CUIF should target |
|---|---|---|
| [CUA-World / Gym-Anything](https://arxiv.org/abs/2604.06126) | Broad software coverage, long-horizon CUA environments, scalable setup/audit pipeline | Not specialized for office artifact structure, layout/template fidelity, editable object constraints, or per-turn office deliverable diagnostics |
| [GDPval](https://arxiv.org/abs/2510.04374) | Economically valuable real work, expert-authored deliverables, human/expert grading | Expensive/coarse grading, not primarily an office-template compliance benchmark, limited focus on interactive revision and structured artifact preservation |
| [PPTArena](https://arxiv.org/abs/2512.03042) | Strong PowerPoint editing benchmark: in-place edits, 100 decks, 2,125 slides, 800+ targeted edits, structural diffs plus rendered slide images and dual VLM judging | Mostly PPTX-specific; CUIF should add multi-turn requirement evolution, cross-file/family workflows, explicit preservation/regression scoring, and GUI-vs-open-tool action-space comparison |
| [OfficeBench](https://arxiv.org/abs/2407.19056) | Multi-application office automation with planning, app switching, and customized task evaluators | Artifact-level layout/style/template scoring is shallow relative to CUIF's intended structured + rendered office checks |
| [OdysseyBench](https://arxiv.org/abs/2508.09124) | Long-horizon office workflows across Word, Excel, PDF, Email, and Calendar; includes real and synthesized task splits | Strong context/memory story, but CUIF should emphasize office artifact fidelity, visual constraints, and per-turn partial credit over PPTX/DOCX/XLSX outputs |
| [SpreadsheetBench](https://arxiv.org/abs/2406.14991) | Real-world spreadsheet manipulation and value-centric XLSX evaluation | Mostly spreadsheet-specific; CUIF should connect source spreadsheets to visual deliverables and evaluate formatting/layout/preservation across files |
| [PPTC-R](https://arxiv.org/abs/2403.03788) | Robustness for PowerPoint task completion, including version updates, multilingual settings, and multi-turn stress | CUIF should avoid primitive API-like tasks and instead use practical layout/template/source-data constraints with richer artifact checks |
| [ParseBench](https://arxiv.org/abs/2604.08538) | Enterprise document parsing dimensions such as tables, charts, semantic formatting, and visual grounding | Parsing is not artifact editing; CUIF can borrow dimension labels but should evaluate production/revision of editable artifacts |

## Action-space framing

The useful comparison is not "visual vs non-visual." It is:

1. **GUI-only track**
   - Agent must use the office GUI through screenshots, mouse, and keyboard.
   - Measures practical desktop CUA behavior, interaction overhead, and spatial manipulation limits.

2. **Open-tool artifact track**
   - Agent may use code, OOXML libraries, parsers, renderers, and GUI tools.
   - Measures the upper bound of office artifact production when agents can operate on structured file internals.

3. **Hybrid/tool-orchestration analysis**
   - The strongest systems may use both: visual inspection/rendering for layout judgment, structured edits for precision, and GUI for unsupported features.

CUIF should report where each action space fails: visual grounding, XML/object manipulation, native editability, collateral damage, turn-state tracking, or final polish.

## Strongest CUIF lane: layout/template/constraint following

The most defensible niche is **layout/template compliance for editable office artifacts**. Example task families:

- Create a deck slide from a rough layout sketch while keeping text boxes, charts, and figures editable.
- Revise an existing slide based on an annotated screenshot without moving non-target objects.
- Apply a government/company template with exact typography, headings, page regions, and required boilerplate.
- Build a native PPTX chart from XLSX data, place it according to a visual reference, and preserve the source workbook.
- Convert a DOCX report section into a deck while preserving citations, figure captions, and brand layout.
- Repair a formatted table or chart after a user asks for a local change in turn 2 without breaking turn-1 requirements.

This lane is practical because real organizations care about templates, public-sector forms, brand compliance, report layout, and clean editable deliverables. It is also technically evaluable through bounding boxes, object trees, text/style checks, chart data checks, rendered image review, and VLM rubrics.

## What the PoC should demonstrate

The PoC does not need broad dataset scale. It should demonstrate that CUIF can generate a diagnostic report for each turn and each constraint type:

- **Content/source fidelity:** required strings, summaries, formulas, cited figures, source data values.
- **Layout fidelity:** object bounding boxes, alignment, spacing, region membership, visual hierarchy.
- **Template/style fidelity:** fonts, colors, theme/master preservation, caption/heading styles.
- **Native editability:** real charts/tables/text boxes where required, not flattened screenshots unless explicitly allowed.
- **Multimodal instruction grounding:** sketch/reference/annotated screenshot constraints satisfied in the artifact.
- **Preservation/collateral damage:** non-target slides/pages/sheets, source files, notes, metadata, and previous-turn constraints unchanged.
- **Turn-level regression:** requirements satisfied in turn 1 remain satisfied after later revisions unless superseded.

## Scaling strategy

The task scale problem should be handled by moving human effort from the instance level to the **template-family level**.

1. **Human-authored template families**
   - A human designs a workflow family: e.g. incident review deck, public report template, KPI briefing, research paper deck, grant one-pager, formatted memo.
   - Each family defines roles, protected regions, visual references, allowed transformations, and evaluator leaves.

2. **Programmatic instantiation**
   - Scripts sample data, names, dates, countries, metrics, colors, layout variants, figure crops, and distractors.
   - Scripts generate seed artifacts, gold intermediate/final artifacts, visual instructions, and evaluator metadata.

3. **Automatic visual constraint generation**
   - Render seed/gold artifacts to images.
   - Overlay annotations, arrows, region boxes, or handwritten-style labels.
   - Generate sketch SVG/PNG references from layout metadata.

4. **Adversarial filtering**
   - Run strong baselines such as frontier open-tool agents and GUI agents.
   - Move too-easy instances to train/dev; keep test instances with non-saturated partial scores.

5. **Human review by sampling**
   - Review every template family.
   - Review sampled instances and all hidden-test families.
   - Avoid full manual annotation for every generated instance.

## Localized artifact direction

Multilingual/localized office artifacts are promising, but should be treated as an extension rather than the main CUIF claim.

A stronger framing than "multilingual" is **jurisdiction-localized document compliance**:

- Korean public-sector HWP/HWPX-style forms and report templates;
- Chinese OFD-style fixed-layout government/financial documents;
- Japanese Ichitaro/JTD-style business or administrative templates;
- locale-specific typography, dates, addresses, seals/stamps, tables, and required boilerplate.

This is attractive because localized document compliance is practical and underexplored. It is risky as the core paper because tooling, licensing, rendering, and evaluator support are much harder than PPTX/DOCX/XLSX. The recommended path is to keep localized artifacts as a small appendix or follow-up benchmark, unless the project obtains reliable parsers/renderers and public-domain templates.

## Recommended paper story

A strong CUIF paper should say:

1. Existing CUA and office benchmarks either optimize broad software coverage, occupational realism, spreadsheet-specific value checks, or PPTX editing; none deeply evaluate interactive layout/template-constrained office artifact production across structured and rendered views.
2. CUIF introduces a task schema for multi-turn, multimodal office artifact constraints where visual instructions are requirements, not just observations.
3. CUIF evaluates with a per-turn requirement tree combining deterministic OOXML/file checks, rendered visual checks, VLM/LLM rubrics, and preservation/regression penalties.
4. CUIF compares GUI-only and open-tool action spaces on the same tasks, revealing when precision editing, visual grounding, preservation, or turn-state tracking is the bottleneck.
5. CUIF scales through template-family generation: human-designed workflow families, executable gold creation, automatic evaluator leaves, and adversarial filtering.
