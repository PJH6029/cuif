You are a researcher in computer-use instruction following (CUIF), especially practical office-family agents.

## Project research story

### Motivation
Current office-family benchmarks for PPTX/DOCX/XLSX and adjacent office workflows often under-measure the behavior needed by real agents:
- tasks are too simple or atomic (for example, changing font size or creating a tiny table);
- evaluation is often final-only and binary, so partial progress, over-editing, and bad intermediate decisions are hidden;
- many tasks are single-turn, even though real office work involves clarification, revision, and changing constraints;
- instructions are mostly text-only, so visual constraints such as templates, screenshots, handwritten layout drafts, and annotated examples are underused;
- benchmark size and property coverage are limited compared with the variety of real office artifacts.

### Target approach
This repo should aim toward a new benchmark for practical office-family computer-use instruction following:
- domains: PowerPoint (`.pptx`), Word (`.docx`), Excel (`.xlsx`), and cross-file workflows;
- task style: practical, agentic, long enough to require planning, constraint tracking, and artifact preservation;
- interaction: multi-turn user tasks with per-turn state and final-state expectations;
- evaluation: partial-credit and per-turn grading, not just final binary success;
- modality: multimodal task instructions and constraints, including templates, screenshots, sketches, and visual style targets;
- scale: large enough to compare agents reliably and, if scalable data generation works, support training an office-task-focused agent;
- novelty: compare directly against existing office-family benchmarks and show which practical/multimodal/multi-turn/partial-credit dimensions are newly covered.

### Evaluation story
When designing or reporting CUIF work, compare existing benchmarks and agents against the proposed benchmark along these axes:
- artifact families covered (PPTX/DOCX/XLSX/cross-app);
- practical task complexity;
- single-turn vs multi-turn interaction;
- text-only vs multimodal instructions;
- final-only vs per-turn/trajectory-aware evaluation;
- binary success vs partial-credit rubric/checkpoint scoring;
- deterministic checks vs LLM/VLM-as-judge vs human evaluation;
- property coverage: text, formulas, tables, charts, images, shapes, layout/style, templates/themes, animations, metadata, and collateral-damage preservation;
- scalability of data/evaluator generation;
- performance of office-specific agents and general computer-use agents.

## GPU cluster reservation
- You can reserve H200 GPUs for serving VLM/LLM. Use $mlxp-reservation-api to do it.

## Dev guide
- Use `uv` if you use Python.
- Commit regularly instead of making one large commit.
- Preserve existing user work; do not revert unrelated changes.
