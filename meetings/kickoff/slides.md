# CUIF Kickoff

## Computer-Use Instruction Following for Visual Artifacts

Benchmarks for agents that edit slides, spreadsheets, and documents under real user constraints.

---

# Kickoff Goals

By the end of this meeting, align on:

- What current computer-use benchmarks measure well.
- Which benchmarks already touch instruction following.
- Why visual artifact instruction following is still under-measured.
- What CUIF should measure first.
- What v0 should include, and who owns the first workstreams.

---

# Starting Hypothesis

Current CUA benchmarks ask:

> Did the agent finish the task?

CUIF should ask:

> Did the agent follow every important instruction and preserve everything it should not touch?

For visual office work, this difference matters.

---

# Current State: General CUA Benchmarks

| Benchmark | Strength | Limitation for CUIF |
| --- | --- | --- |
| OSWorld | Real desktop tasks, broad app coverage, executable evaluators | Office tasks are mostly endpoint success or reference comparison |
| WindowsAgentArena | Scalable Windows CUA, realistic UI grounding | Limited rich artifact scoring in current office tasks |
| OfficeBench | Multi-app office workflows | Tool/API workflow, coarse output checks |
| OdysseyBench | Long-horizon memory/RAG office workflows | Memory-focused, not visual fidelity-focused |
| OSUniverse | GUI navigation/task taxonomy | Not centered on office artifact outputs |

Takeaway: environment realism is improving, but instruction-level artifact diagnostics are thin.

---

# Current State: Visual Artifact Benchmarks

| Area | Representative benchmarks | What they measure |
| --- | --- | --- |
| Slides | PPTArena, PresentBench, SlidesBench, SlidesGen-Bench, DeckBench | Editing, generation, visual quality, content grounding, preferences |
| Spreadsheets | SpreadsheetBench, SpreadsheetBench 2, SheetCopilot, SheetAgent | Functional correctness, workflows, charts, formatting, agent execution |
| Documents | DocEdit, DocEdit-v2, OfficeBench/OdysseyBench document tasks | Localized edit commands, structure editing, text/file outcome checks |

Takeaway: artifact benchmarks are richer than general CUA benchmarks, but most are not full CUA instruction-following benchmarks.

---

# Closest Benchmarks To Our Goal

**PPTArena**

- Best match for in-place visual slide editing.
- Separates instruction-following and visual-quality scores.
- Uses structured PPTX diffs plus rendered images.

**PPTC / PPTC-R**

- Explicit PowerPoint position restrictions.
- Robustness variants: paraphrase, noise, multilingual, API changes.

**PresentBench**

- Fine-grained binary checklist scoring for slide generation.
- Strong model for constraint-level rubrics.

---

# More Relevant Pieces

**SpreadsheetBench 2**

- Professional spreadsheet deliverables.
- Exact cell/workbook preservation for modeling/debugging.
- VLM checklist scoring for visualizations.

**DocEdit / DocEdit-v2**

- Localized document edit requests.
- Bounding boxes, target objects, document layout, style replication.

**DeckBench**

- Multi-turn slide editing workflow.
- Useful for revision trajectories, but less atomic in constraint scoring.

---

# The Core Gap

No current benchmark fully combines:

- Real or realistic computer-use workflows.
- Native visual artifacts: PPTX, XLSX, DOCX.
- Text plus visual instructions.
- Region/pointing requests.
- Constraint-level ground truth.
- Preservation and no-extra-edit scoring.
- Deterministic file checks plus rendered appearance checks.

That is the CUIF opportunity.

---

# What Counts As Instruction Following?

Instruction following is not just text content.

It includes:

- Typography: font, size, weight, color.
- Layout: alignment, position, margins, overlap.
- Visual references: match this template or screenshot.
- Spatial references: top-right image, chart below the title.
- Spreadsheet semantics: formulas, charts, pivots, conditional formatting.
- Preservation: keep everything else unchanged.
- Negative constraints: do not use red, do not change slide 1.
- Multi-turn corrections: undo only one change.

---

# Why Visual Artifact IF Is Hard

Correctness lives in two places:

- Native structure: XML, formulas, charts, masters, styles, runs.
- Rendered appearance: what users actually see.

Common failures:

- Correct text, wrong style.
- Correct object, wrong location.
- Correct chart image, broken editable chart.
- Correct target edit, extra unrelated changes.
- Good-looking output, but no native structure left.

---

# Evaluation Lessons

Prior work points toward a layered evaluator:

1. Parse native artifacts.
2. Render pages, slides, sheets, and charts.
3. Apply deterministic checks wherever possible.
4. Use binary checklist items for task-specific constraints.
5. Use VLM judges only for semantic or aesthetic criteria.
6. Report per-constraint results, not only task success.

Principle: VLM-as-judge should be scoped, auditable, and not used for measurable facts.

---

# Proposed CUIF Task Unit

Each task should include:

- Initial artifact or desktop state.
- User instruction.
- Optional visual reference, screenshot, crop, or bounding box.
- Hidden typed constraints.
- Expected output artifact.
- Optional reference artifact, but not as the only ground truth.

Example hidden constraint:

```json
{
  "target": "slide 3 top-right image",
  "operation": "resize",
  "checks": [
    "area >= 1.35x original",
    "aspect ratio preserved",
    "within canvas",
    "no overlap with text",
    "all other slides unchanged"
  ]
}
```

---

# Proposed v0 Domains

Start narrow enough to build a real evaluator.

**Phase 1**

- PPTX slide editing.
- XLSX spreadsheet editing and visualization.

**Phase 2**

- DOCX document layout and PDF export.
- Cross-artifact tasks: spreadsheet to slide, report to PDF, chart to deck.

Reasoning: PPTX and XLSX have the richest existing benchmarks and the clearest user pain.

---

# Proposed Scoring

Report multiple scores:

- Task success: all critical constraints pass.
- Constraint pass rate: passed / valid constraints.
- Hard constraint pass rate.
- Preservation score.
- Visual fidelity score.
- Editability/native-structure score.
- Robustness score across paraphrase, noise, visual reference, and multilingual variants.
- Turn-level and session-level scores for multi-turn tasks.

The leaderboard should reveal what an agent fails at.

---

# Baseline Families

We should compare:

- GUI-only CUA agents.
- Direct file-editing agents using Python libraries.
- Hybrid agents with GUI plus file introspection.
- Structure-aware PPTX/XML agents.
- Spreadsheet code agents with execution feedback.
- Product/commercial baselines where allowed.
- Human expert calibration.

This avoids rewarding only one interaction style.

---

# v0 Data Plan

Build a small diagnostic seed set before scaling.

Suggested v0:

- 50 PPTX tasks.
- 40 XLSX tasks.
- 10 mixed or multi-turn stress tests.

For each task:

- 8 to 20 atomic constraints.
- At least 2 preservation constraints.
- At least 1 spatial or visual-reference constraint where possible.
- Human review for ambiguity and valid alternatives.

---

# Risks

**Evaluator brittleness**

Native office formats have messy XML and library gaps.

**Ambiguous instructions**

Realistic prompts can be underspecified.

**VLM judge variance**

Broad visual judgments may drift.

**Overfitting to one artifact format**

PPTX is tempting, but CUIF should generalize.

---

# Mitigations

- Use typed constraints with explicit tolerances.
- Keep VLM judgments binary and narrow.
- Store rendered artifacts, prompts, judge outputs, and diffs.
- Validate tasks with at least two humans or one human plus deterministic review.
- Report category-level scores.
- Include multiple valid references only where needed.
- Make preservation a first-class score.

---

# Kickoff Decisions

Decide today:

- Is v0 PPTX + XLSX, or PPTX-only first?
- Do we require real GUI interaction, direct file editing, or both?
- What is the first constraint taxonomy?
- Which evaluator layer do we prototype first?
- What baselines are must-have?
- What is the first public milestone?

---

# Next 4 Weeks

Week 1:

- Freeze v0 benchmark spec and constraint taxonomy.

Week 2:

- Build 15 to 20 seed tasks and parser/render prototypes.

Week 3:

- Run two baseline families and inspect failures.

Week 4:

- Revise schema, publish internal v0.1 report, choose scale-up plan.

---

# Working Definition

CUIF measures whether a computer-use agent can:

1. Understand text and visual instructions.
2. Locate the intended object or region.
3. Apply the requested edit.
4. Preserve unrelated content.
5. Produce a native, usable artifact.
6. Do this robustly across realistic variants.

That is the benchmark gap we can own.

---

# References To Keep Open

- OSWorld: https://os-world.github.io/
- WindowsAgentArena: https://microsoft.github.io/WindowsAgentArena/
- OfficeBench: https://github.com/zlwang-cs/OfficeBench
- SpreadsheetBench: https://spreadsheetbench.github.io/
- PPTArena: https://github.com/michaelofengend/PPTArena
- PresentBench: https://presentbench.github.io/
- DocEdit: https://github.com/adobe-research/DocEdit-Dataset
- Full review: `../../report.md`

