# CUIF Kickoff Slide Outline

Working title: **CUIF: Computer-Use Instruction Following for Visual Artifacts**

Audience: project collaborators and early advisors.

Tone: crisp research kickoff, problem-first, opportunity-oriented.

Meeting goal: leave with agreement on the benchmark gap, v0 scope, evaluation philosophy, and immediate workstreams.

## 1. Title

Key message: CUIF targets a missing benchmark intersection: computer-use agents, visual office artifacts, and instruction/constraint following.

## 2. Kickoff Goals

Key message: This meeting should align the team on the problem, evidence, opportunity, and first build decisions.

## 3. Starting Hypothesis

Key message: Existing computer-use benchmarks mostly measure task completion, while real office work demands constraint following, visual fidelity, and preservation.

## 4. What Current CUA Benchmarks Measure

Key message: OSWorld, WindowsAgentArena, OfficeBench, and OdysseyBench are strong for environment/task realism, but they are not built around visual artifact constraints.

## 5. What Visual Artifact Benchmarks Measure

Key message: Slide and spreadsheet benchmarks increasingly evaluate generated artifacts, but often through reference similarity, broad quality, or functional correctness.

## 6. Closest Instruction-Following Benchmarks

Key message: PPTArena, PPTC/PPTC-R, PresentBench, SpreadsheetBench 2, and DocEdit each capture part of the desired benchmark, but none covers the full CUIF target.

## 7. More Relevant Pieces

Key message: SpreadsheetBench 2, DocEdit, DocEdit-v2, and DeckBench add important ideas for visualization scoring, localization, style replication, and multi-turn revision.

## 8. The Core Gap

Key message: No benchmark unifies real or realistic computer-use workflows with fine-grained instruction-following scores over native visual artifacts.

## 9. What "Instruction Following" Means Here

Key message: Constraints can be textual, visual, spatial, preservation-oriented, negative, or multi-turn.

## 10. Why Visual Artifact IF Is Hard

Key message: Correctness lives in both native file structure and rendered appearance, and many failures are extra-edit or preservation failures.

## 11. Evaluation Lessons From Prior Work

Key message: The right evaluator should combine deterministic artifact parsing, rendering, checklist scoring, and tightly scoped VLM judgment.

## 12. Proposed CUIF Task Unit

Key message: Each task should pair initial state, user instruction, optional visual reference, hidden typed constraints, and output artifact.

## 13. Proposed Domains for v0

Key message: Start with PPTX and XLSX, add DOCX once the parser/evaluator story is stable.

## 14. Proposed Scoring

Key message: Report task success, constraint pass rate, preservation, editability, visual fidelity, robustness, and turn/session scores.

## 15. Baseline Families

Key message: Compare GUI agents, direct file-editing agents, hybrid agents, structure-aware XML agents, and product baselines where allowed.

## 16. v0 Data Plan

Key message: Build a small but diagnostic seed set before scaling: real templates, synthetic perturbations, typed constraints, and human validation.

## 17. Risks

Key message: The hardest risks are evaluator brittleness, VLM judge variance, ambiguous instructions, and native artifact complexity.

## 18. Mitigations

Key message: Typed constraints, narrow judges, stored diffs, and category-level scores make the benchmark auditable.

## 19. Kickoff Decisions

Key message: Decide scope, artifacts, constraint taxonomy, evaluation stack, baselines, and milestone ownership.

## 20. Next 4 Weeks

Key message: Move from literature review to a concrete v0 benchmark spec, seed tasks, evaluator prototype, and baseline harness.

## 21. Working Definition

Key message: CUIF should measure whether agents understand instructions, locate targets, edit correctly, preserve unrelated content, and produce usable native artifacts.

## 22. References

Key message: Point collaborators back to the full literature review and core benchmark sources.
