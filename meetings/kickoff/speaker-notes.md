# CUIF Kickoff Speaker Notes

Use these notes as the presenter talk track for `slides.md`.

## Slide 1: Title

Frame CUIF as a benchmark at the intersection of computer-use agents and visual office artifacts. The important phrase is "instruction following", not just "task completion".

## Slide 2: Kickoff Goals

Set expectations that this is a decision meeting. The goal is not to review every benchmark in detail; the goal is to choose the first shape of our own benchmark.

Discussion prompt:

- What decisions must be made before anyone can start building tasks?

## Slide 3: Starting Hypothesis

Emphasize that visual office work is constraint-heavy. A slide can be "completed" while still violating the user request if it changes the wrong object, uses the wrong font, or breaks unrelated layout.

## Slide 4: General CUA Benchmarks

OSWorld and WindowsAgentArena are important because they make agents operate real environments. OfficeBench and OdysseyBench are important because they model office workflows. The limitation is that their endpoint evaluators usually do not diagnose fine-grained visual constraints.

## Slide 5: Visual Artifact Benchmarks

The slide/spreadsheet/document communities have useful pieces. The split is the problem: artifact benchmarks may not be computer-use benchmarks, and computer-use benchmarks may not be artifact-fidelity benchmarks.

## Slide 6: Closest Benchmarks

PPTArena is the strongest predecessor for slide editing. PPTC and PPTC-R are useful for explicit position constraints and robustness. PresentBench gives us a checklist model that should transfer well.

Discussion prompt:

- Do we want CUIF to look more like PPTArena plus other artifacts, or more like OSWorld plus deeper artifact scoring?

## Slide 7: More Relevant Pieces

SpreadsheetBench 2 matters because it introduces business spreadsheet deliverables and preservation. DocEdit matters because it makes localization and edit commands explicit. DeckBench matters for multi-turn editing.

## Slide 8: The Core Gap

This is the thesis slide. There is no benchmark that combines realistic CUA, native artifacts, multimodal instructions, typed constraints, preservation, deterministic checks, and rendered appearance.

## Slide 9: What Counts As Instruction Following?

Make the taxonomy concrete. Use examples:

- "Use Calibri 18 pt for body text."
- "Match this template."
- "Make the top-right image bigger."
- "Do not change the title slide."

## Slide 10: Why It Is Hard

Stress native structure versus rendered appearance. A screenshot can look correct while the editable chart is broken. A workbook can have correct values while the conditional formatting was missed.

## Slide 11: Evaluation Lessons

The main claim: deterministic checks should own measurable constraints. VLMs are for semantics and aesthetics, not for counting font sizes or formula ranges.

## Slide 12: Proposed Task Unit

This is the first concrete design proposal. The hidden typed constraints are the key artifact. Reference files are useful, but should not be the only source of truth.

Discussion prompt:

- What should the minimum viable constraint schema include?

## Slide 13: Proposed v0 Domains

Recommend PPTX + XLSX first. PPTX gives visual layout and images. XLSX gives formulas, charts, formatting, and preservation. DOCX should come next, but native document layout evaluation will be slower to stabilize.

## Slide 14: Proposed Scoring

The leaderboard should be diagnostic. A single success score hides too much. We need to know whether systems fail at localization, typography, chart semantics, preservation, or native editability.

## Slide 15: Baseline Families

This slide prevents benchmark bias. If only GUI agents are allowed, file-editing agents cannot compete. If only direct file editing is allowed, computer-use agents are not measured. CUIF can allow both and label them clearly.

## Slide 16: v0 Data Plan

Keep v0 small and sharp. A 100-task seed with 8 to 20 constraints per task can produce enough diagnostic signal to validate the evaluator before scaling.

## Slide 17: Risks

Evaluator brittleness is the biggest engineering risk. Ambiguity is the biggest benchmark validity risk. VLM judge variance is the biggest reproducibility risk.

## Slide 18: Mitigations

The mitigation theme is transparency: typed constraints, stored diffs, rendered artifacts, judge outputs, and category-level scores.

## Slide 19: Kickoff Decisions

Use this as the working agenda for the final 15 minutes. The most important decision is whether v0 is PPTX-only or PPTX + XLSX.

Suggested default:

- v0: PPTX + XLSX.
- Interaction modes: direct file editing and GUI/hybrid both allowed, tagged separately.
- Evaluator prototype: PPTX parser/render/diff first, XLSX parser/checks second.

## Slide 20: Next 4 Weeks

Make the next steps concrete. End with owners, not general interest.

Suggested workstreams:

- Benchmark spec and taxonomy.
- PPTX evaluator prototype.
- XLSX evaluator prototype.
- Seed task authoring.
- Baseline harness.

## Slide 21: Working Definition

Close by repeating the benchmark identity. CUIF is about following the full user intent in visual artifacts, including what must not change.

## Slide 22: References

Point people to `../../report.md` for the full literature review and code-inspection details.

