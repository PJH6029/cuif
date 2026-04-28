# PoC task generation guide

Use this guide to hand-author **2--3 complete CUIF PoC tasks** after choosing only a task topic. A complete task is not just an instruction: it is a runnable package with a manifest, seed/input artifacts, gold/reference artifacts, deterministic smoke outputs, scoring checks, and review targets that the current evaluator can validate.

The current PoC is **PPTX-first**. You may use DOCX/XLSX/images as source/context artifacts, but the primary evaluated output should be a `.pptx` unless you also add evaluator support for other artifact families.

## What one complete task contains

A complete task lives under `poc/tasks/<task_id>/` and has this shape:

```text
poc/tasks/<task_id>/
  manifest.yaml
  artifacts/
    seed.pptx                 # initial editable office artifact
    inputs/
      sketch.png|svg          # optional visual instruction/reference
      data.xlsx|json|txt      # optional source data/context
      style_reference.png     # optional visual style target
    gold/
      turn1.pptx              # ideal artifact after turn1
      final.pptx              # ideal artifact after the final turn
  mock_outputs/
    turn1/
      result.pptx             # deterministic smoke output copied by mock adapter
    final/
      result.pptx
```

Minimum viable task package:

- `manifest.yaml` validates with `uv run cuif-eval validate`.
- Every `artifacts.package.*.path` file exists and is immutable task input/reference material.
- Every `artifacts.expected_outputs.<turn>.<name>` path can be produced by an adapter.
- `mock_outputs/<turn>/result.pptx` exists for every turn so the task can run in CI/local smoke mode.
- At least two turns exist: one creation/edit turn and one revision/preservation turn.
- Checks include partial-credit requirements for content, layout/style, and collateral-damage preservation.
- `review.comparison_targets` includes seed, per-turn outputs, and gold final.

## Authoring rule of thumb

After choosing a topic, keep the task small enough that a human can create the seed/gold files in 30--60 minutes, but rich enough to show why CUIF is different from atomic office benchmarks:

- **Practical**: framed like real office work, not a single formatting command.
- **Multi-turn**: turn 2 revises turn 1 and has to preserve something.
- **Multimodal**: include at least one sketch, screenshot, style reference, or source artifact when possible.
- **Partial-credit**: decompose success into 8--15 checkable requirements.
- **Preservation-aware**: explicitly protect non-target slides/regions/text.

For the first manual batch, prefer 2--3 PPTX tasks that vary in topic and property coverage rather than trying to cover PPTX/DOCX/XLSX equally.

## Step 1: Choose and scope a task topic

Fill this topic card before making files:

```text
Task topic:
Real-world scenario:
User goal:
Primary output: PPTX deck
Seed artifact contents:
Turn 1 request:
Final turn request:
Protected content/regions:
Multimodal/source inputs:
What should be graded deterministically:
What should be judged visually or semantically:
```

Good PoC topics:

1. **Product launch mini-deck**: turn a rough seed into a 3-slide launch update, then apply brand styling while preserving an appendix slide.
2. **Research group progress deck**: build a dashboard from short bullet/data inputs, then revise layout to match a screenshot/sketch.
3. **Quarterly sales summary**: create a chart-like dashboard slide from a small table, then update one metric and preserve prior narrative text.
4. **Workshop handout deck**: organize agenda/outcomes/next steps, then adapt it for executives without damaging hidden notes or an invariant slide.
5. **Grant pitch one-pager deck**: create a single-slide visual pitch from a sketch, then enforce typography/color constraints.

Avoid first-batch topics that require heavy chart parsing, animations, macros, embedded videos, or evaluator behavior not implemented yet.

## Step 2: Define turns before creating artifacts

Recommended shape for one PoC task:

### Turn 1: create or restructure

Ask the agent to transform the seed into a meaningful intermediate artifact. Include concrete content and layout requirements.

Example:

```text
Create a three-slide product launch update from the seed deck.
Slide 1 should be an executive summary with the title "Atlas Launch Readiness".
Slide 2 should show three readiness pillars: Demand, Product, and Support.
Slide 3 is protected benchmark context; keep it unchanged.
Use the attached sketch as the intended slide 1 layout.
```

### Final turn: revise while preserving

Ask for an incremental update that tests multi-turn state tracking and collateral-damage avoidance.

Example:

```text
Apply the CUIF brand style to the slide 1 title: blue #1F4E79, bold, 34 pt.
Move the risk callout into the lower-right region of slide 1.
Keep the turn 1 content and preserve slide 3 exactly.
```

Guidelines:

- Use stable text strings that checks can search for.
- Include at least one preservation instruction in the final turn.
- Make each turn produce the same output name (`result.pptx`) unless there is a strong reason not to.
- Do not hide essential requirements only in a gold file; the manifest checks should reflect them.

## Step 3: Create source and reference artifacts

Create artifacts manually in PowerPoint, LibreOffice Impress, Keynote exported to PPTX, or a small script using `python-pptx`. Prefer editable PPTX shapes/text over screenshots flattened into images.

### Seed deck

The seed should include enough context to make the task realistic but not so much that authoring is slow.

Suggested seed contents:

- A title or context slide with rough/raw content.
- One or more editable text boxes that the agent should reuse.
- A protected slide or object containing a sentinel string such as `Do not edit: <task invariant>`.
- Optional unfinished layout placeholders to make the transformation visible.

### Input artifacts

Put multimodal/source artifacts under `artifacts/inputs/` and declare them in the manifest. Examples:

- `sketch.png` or `sketch.svg`: a rough layout target.
- `style_reference.png`: screenshot with target colors/visual hierarchy.
- `source_data.xlsx`, `source_data.json`, or `brief.txt`: small source material the instruction references.
- `reference_deck.pptx`: optional style source, if it is immutable context rather than output.

### Gold artifacts

Gold files should be human-authored ideal outputs:

- `artifacts/gold/turn1.pptx`: expected state after turn 1.
- `artifacts/gold/final.pptx`: expected final state.

The evaluator does not automatically grade against gold unless you write checks that reference gold, but gold is important for review UI and author sanity.

### Mock outputs

For deterministic smoke runs, copy gold artifacts into `mock_outputs`:

```bash
mkdir -p poc/tasks/<task_id>/mock_outputs/{turn1,final}
cp poc/tasks/<task_id>/artifacts/gold/turn1.pptx poc/tasks/<task_id>/mock_outputs/turn1/result.pptx
cp poc/tasks/<task_id>/artifacts/gold/final.pptx poc/tasks/<task_id>/mock_outputs/final/result.pptx
```

This does not make the task benchmark-quality; it makes the evaluator path runnable before real agents are integrated.

## Step 4: Create the folder skeleton

```bash
TASK_ID=<snake_case_task_id>
mkdir -p "poc/tasks/${TASK_ID}/artifacts/inputs"
mkdir -p "poc/tasks/${TASK_ID}/artifacts/gold"
mkdir -p "poc/tasks/${TASK_ID}/mock_outputs/turn1"
mkdir -p "poc/tasks/${TASK_ID}/mock_outputs/final"
```

Naming conventions:

- Use lowercase snake_case for task IDs, turn IDs, output IDs, artifact IDs, and check IDs.
- Use `turn1` and `final` for the first manual PoC batch unless a task truly needs more turns.
- Use `result` as the output ID and `result.pptx` as the produced file name.
- Keep check IDs globally unique within the manifest, not only within each turn.

## Step 5: Write `manifest.yaml`

Start from this template and replace every placeholder. Keep it YAML/JSON-compatible: simple strings, lists, mappings, numbers, and booleans.

```yaml
manifest_version: "0.1"
id: <task_id>
title: <Human readable title>
primary_artifact_family: pptx
artifact_families: [pptx]
tracks: [open_tool, gui]
scoring:
  policy: sum_points
judge:
  api_key_env: OPENAI_API_KEY
artifacts:
  package:
    seed:
      path: artifacts/seed.pptx
      type: pptx
      role: seed
    sketch:
      path: artifacts/inputs/sketch.png
      type: image
      role: instruction_input
    gold_turn1:
      path: artifacts/gold/turn1.pptx
      type: pptx
      role: gold
    gold_final:
      path: artifacts/gold/final.pptx
      type: pptx
      role: gold
  expected_outputs:
    turn1:
      result:
        path: result.pptx
        type: pptx
    final:
      result:
        path: result.pptx
        type: pptx
turns:
  - id: turn1
    new_inputs:
      textual: []
      visual:
        - package.sketch
    instruction: >-
      <Turn 1 instruction. Mention seed deck and input artifacts by natural language.
      Include exact required text strings and any protected content.>
    expected_output: result
    checks:
      - id: turn1_file_exists
        evaluator: file_exists
        artifact: run.outputs.turn1.result
        points: 1
      - id: turn1_slide_count
        evaluator: pptx_slide_count
        artifact: run.outputs.turn1.result
        points: 1
        depends_on: [turn1_file_exists]
        params: {count: 3}
      - id: turn1_title_present
        evaluator: pptx_text_contains
        artifact: run.outputs.turn1.result
        points: 2
        depends_on: [turn1_file_exists]
        params: {text: "<Exact expected title>"}
      - id: turn1_title_region
        evaluator: pptx_bbox_region
        artifact: run.outputs.turn1.result
        points: 2
        depends_on: [turn1_title_present]
        params:
          selector: {slide: 1, text_contains: "<Exact expected title>"}
          region: {slide: 1, x_min: 0.05, y_min: 0.05, x_max: 0.95, y_max: 0.25}
          tolerance: 0.02
      - id: turn1_rendered_review
        evaluator: rendered_layout_review
        artifact: run.outputs.turn1.result
        points: 0
        optional: true
        diagnostic: true
        params:
          note: Optional rendered smoke check for author review.
  - id: final
    new_inputs:
      textual: []
      visual: []
    instruction: >-
      <Final turn instruction. Apply one style/layout/content change and explicitly
      preserve selected turn1 content or protected slide/object text.>
    expected_output: result
    checks:
      - id: final_file_exists
        evaluator: file_exists
        artifact: run.outputs.final.result
        points: 1
      - id: final_slide_count
        evaluator: pptx_slide_count
        artifact: run.outputs.final.result
        points: 1
        depends_on: [final_file_exists]
        params: {count: 3}
      - id: final_title_present
        evaluator: pptx_text_contains
        artifact: run.outputs.final.result
        points: 2
        depends_on: [final_file_exists]
        params: {text: "<Exact expected title>"}
      - id: final_title_style
        evaluator: pptx_style_check
        artifact: run.outputs.final.result
        points: 3
        depends_on: [final_title_present]
        params:
          selector: {slide: 1, text_contains: "<Exact expected title>"}
          font_color: "#1F4E79"
          font_size_pt: 34
          font_size_tolerance: 0.25
          bold: true
      - id: final_protected_slide_preserved
        evaluator: pptx_preservation_diff
        artifact: run.outputs.final.result
        points: 3
        depends_on: [final_slide_count]
        params:
          reference: run.outputs.turn1.result
          compare: exact_slide_text
          slides: [3]
          protected_texts: ["<Protected sentinel text>"]
      - id: final_title_layout_preserved
        evaluator: pptx_preservation_diff
        artifact: run.outputs.final.result
        points: 2
        depends_on: [final_title_style]
        params:
          reference: run.outputs.turn1.result
          selector: {slide: 1, text_contains: "<Exact expected title>"}
          tolerance: 0.02
      - id: optional_llm_summary_judge
        evaluator: llm_text_rubric
        artifact: run.outputs.final.result
        points: 0
        optional: true
        diagnostic: true
        params:
          prompt: "Check whether the final deck satisfies the task topic and preserves protected context."
          rubric: "Pass if the deck contains the required topic-specific content and no protected context is removed."
      - id: optional_vlm_layout_judge
        evaluator: vlm_layout_rubric
        artifact: run.outputs.final.result
        points: 0
        optional: true
        diagnostic: true
        params:
          prompt: "Inspect the rendered final deck layout."
          rubric: "Pass if the rendered PNG previews visually match the requested hierarchy and no obvious layout damage appears."
# Review HTML is generated automatically from the task trajectory:
# - top row: package.seed -> package.gold_turn1 -> ... -> package.gold_final
# - bottom row: empty seed-output placeholder -> run.outputs.turn1.<expected_output>
#   -> ... -> run.outputs.final.<expected_output>
#
# Prefer conventional gold artifact names (`gold_turn1`, `gold_turn2`,
# `gold_final`) plus declared `turns[].expected_output`. The optional legacy
# `review.comparison_targets` list is only needed for custom/extra comparison
# targets; standard seed/gold/output trajectory review does not require it.
```

If a task has no sketch, remove the `sketch` artifact entry instead of pointing it at a missing file.

Every agent-facing package artifact with role `source_input`, `instruction_input`, or `style_input` must be revealed by exactly one turn under `turns[].new_inputs`. Use `textual` for text/data/document inputs such as `.txt`, `.json`, `.xlsx`, `.docx`, or `.pdf`, and `visual` for image/sketch/screenshot/style targets such as `.png`, `.svg`, or `image`. Do not list future-turn artifacts in earlier turns; the external bundle flow uses this field to copy only the active turn's new inputs into `current/inputs/<turn>/`.

Supported package artifact `type` values today are `pptx`, `docx`, `xlsx`, `pdf`, `image`, `svg`, `png`, `json`, and `txt`; output artifact `type` values are `pptx`, `docx`, `xlsx`, `image`, `json`, and `txt`. If you include DOCX/XLSX/PDF as context, keep PPTX as the evaluated output unless new deterministic checks are added.

## Step 6: Pick deterministic checks

Current supported evaluator names:

| Evaluator | Use when | Important params |
| --- | --- | --- |
| `file_exists` | Prove adapter created the expected output. | none |
| `pptx_slide_count` | Require exact slide count. | `count` |
| `pptx_text_contains` | Require one or more exact/near-exact strings. | `text` or `texts`, optional `case_sensitive` |
| `pptx_bbox_region` | Require a shape/text box to stay inside a normalized slide region. | `selector`, `region`, optional `tolerance` |
| `pptx_style_check` | Require font color, size, and/or bold on selected text. | `selector`, `font_color`, `font_size_pt`, `font_size_tolerance`, `bold` |
| `pptx_chart_data` | Require a native PowerPoint chart to contain expected chart type, categories, series names, and values. | `selector`, optional `chart_type`, `categories`, `series`, `value_tolerance` |
| `pptx_image_count` | Require one or more embedded raster images on a slide. | `selector`, optional `count` or `min_count` |
| `pptx_image_match` | Require an embedded raster image to visually match a package reference crop and optionally sit in a region. | `source`, `selector`, optional `min_similarity`, `region`, `tolerance` |
| `pptx_formula_present` | Require a formula string in PPTX text with whitespace/math-symbol normalization and optional region check. | `formula` or `formulas`, optional `selector`, `region`, `tolerance` |
| `pptx_preservation_diff` | Detect collateral damage to protected text or selected shape layout. | `reference`, optional `compare`, `slides`, `protected_texts`, `selector`, `tolerance` |
| `rendered_layout_review` | Generate PNG/fallback preview as an evaluator-visible diagnostic. | any note metadata; usually `optional: true`, `diagnostic: true`, `points: 0` |
| `rendered_image_similarity` | Alias of `rendered_layout_review` in the current PoC. | same as above |
| `llm_text_rubric` | Optional text/semantic judge over structured artifact summary. | `prompt`, `rubric`, optional `model`, `base_url` |
| `vlm_layout_rubric` | Optional rendered PNG layout judge. | `prompt`, `rubric`, optional `model`, `base_url`, `image_url_base` |

### Artifact references

Use only these namespaces in checks and review targets:

- `package.<artifact_id>` for immutable task artifacts declared under `artifacts.package`.
- `run.outputs.<turn_id>.<output_id>` for adapter-produced outputs declared under `artifacts.expected_outputs`.

Do **not** declare generated reports, previews, `output/`, or `run/` files as package artifacts.

### Selectors and normalized regions

PPTX selectors currently support:

```yaml
selector:
  slide: 1                  # optional 1-indexed slide number
  text_contains: "Title"    # optional substring match
  name: "Rectangle 4"       # optional PowerPoint shape name
```

Regions use normalized slide coordinates where `(0, 0)` is top-left and `(1, 1)` is bottom-right:

```yaml
region:
  slide: 1
  x_min: 0.05
  y_min: 0.05
  x_max: 0.95
  y_max: 0.25
tolerance: 0.02
```

Authoring tip: use broad regions for hand-made tasks. A too-tight bounding-box check will fail for harmless differences between PowerPoint, LibreOffice, and agent tooling.

### Preservation checks

Use `pptx_preservation_diff` for two common cases:

Protect exact text on non-target slides:

```yaml
params:
  reference: run.outputs.turn1.result
  compare: exact_slide_text
  slides: [3]
  protected_texts: ["Do not edit: launch readiness invariant"]
```

Protect a selected object's layout between turns:

```yaml
params:
  reference: run.outputs.turn1.result
  selector: {slide: 1, text_contains: "Atlas Launch Readiness"}
  tolerance: 0.02
```

Prefer using `run.outputs.turn1.result` as the final-turn preservation reference because it tests whether the final turn preserved the actual prior state. Use `package.seed` or `package.gold_turn1` only when that is the intended reference.

## Step 7: Allocate points

Use enough points to make partial credit meaningful but not noisy. A good two-turn PoC task often has 18--25 required points plus optional 0-point diagnostics.

Suggested distribution:

| Requirement type | Points |
| --- | ---: |
| Output exists / file contract | 1 per turn |
| Slide count / basic structure | 1--2 per turn |
| Required content strings | 1--3 each |
| Layout regions | 2--3 each |
| Style constraints | 2--4 total |
| Preservation / collateral damage | 3--6 total |
| Optional rendered or judge diagnostics | 0 initially |

Dependency pattern:

- Layout/style checks should depend on the text/content check for the object they select.
- Preservation checks should depend on basic output existence and slide count.
- Do not make every check depend on every prior check; preserve independent partial credit.

Example:

```yaml
- id: final_title_style
  depends_on: [final_title_present]
- id: final_protected_slide_preserved
  depends_on: [final_slide_count]
```

## Step 8: Add optional judge checks carefully

For the first manual tasks, use judges as **optional 0-point diagnostics** unless you are explicitly studying live-judge scoring. This keeps deterministic smoke tests stable.

Text judge example:

```yaml
- id: optional_llm_topic_judge
  evaluator: llm_text_rubric
  artifact: run.outputs.final.result
  points: 0
  optional: true
  diagnostic: true
  params:
    prompt: "Check whether the deck communicates the launch-readiness story."
    rubric: "Pass if the deck includes launch status, risks, and next steps in a coherent executive-summary format."
```

VLM judge example:

```yaml
- id: optional_vlm_layout_judge
  evaluator: vlm_layout_rubric
  artifact: run.outputs.final.result
  points: 0
  optional: true
  diagnostic: true
  params:
    prompt: "Inspect the rendered final deck."
    rubric: "Pass if slide 1 has a clear title hierarchy, no major overlaps, and the risk callout is in the lower-right region."
```

Live OpenAI-compatible judge smoke is optional:

```bash
npx openai-oauth
uv run cuif-eval run \
  --task poc/tasks/<task_id> \
  --adapter mock \
  --out output/runs/<task_id>_judge \
  --judge-base-url http://127.0.0.1:<port>/v1 \
  --judge-model <model>
```

For true `openai-oauth` VLM image tests, PNG previews must be reachable through an `http`/`https` URL:

```bash
uv run cuif-eval run \
  --task poc/tasks/<task_id> \
  --adapter mock \
  --out output/runs/<task_id>_judge \
  --judge-base-url http://127.0.0.1:<port>/v1 \
  --judge-model <model> \
  --judge-image-url-base https://<public-host>/<task_id>_judge
```

If no live judge is intended, always use `--skip-judges` in smoke commands.

## Step 9: Validate and run the smoke path

Validate the manifest:

```bash
uv run cuif-eval validate poc/tasks/<task_id>/manifest.yaml
```

Run the deterministic mock smoke:

```bash
uv run cuif-eval run \
  --task poc/tasks/<task_id> \
  --adapter mock \
  --out output/runs/<task_id>_mock \
  --skip-judges
```

Inspect generated files:

```bash
ls output/runs/<task_id>_mock
ls output/runs/<task_id>_mock/outputs/turn1
ls output/runs/<task_id>_mock/outputs/final
sed -n '1,200p' output/runs/<task_id>_mock/report.md
```

Expected run outputs:

```text
output/runs/<task_id>_mock/
  report.json
  report.md
  review/index.html
  outputs/turn1/result.pptx
  outputs/final/result.pptx
  previews/...
  judge_cache/...
  logs/...
```

If the score is not full on copied gold/mock outputs, fix the manifest checks or gold files before asking any agent to attempt the task.

## Step 10: Prepare a manual/human run if needed

The manual adapter writes turn instructions and prepares a workspace; it does not evaluate until outputs are placed.

```bash
uv run cuif-eval run \
  --task poc/tasks/<task_id> \
  --adapter manual \
  --out output/runs/<task_id>_manual
```

Then create these files manually:

```text
output/runs/<task_id>_manual/outputs/turn1/result.pptx
output/runs/<task_id>_manual/outputs/final/result.pptx
```

Evaluate the completed manual run:

```bash
uv run cuif-eval evaluate \
  --task poc/tasks/<task_id> \
  --run output/runs/<task_id>_manual \
  --skip-judges
```

## Step 11: Author review checklist

Before considering a task complete, verify:

- [ ] `manifest.yaml` validates.
- [ ] All declared `artifacts.package` paths exist.
- [ ] No package artifact points into generated run/report/preview paths.
- [ ] Seed, gold, and mock output PPTX files open in PowerPoint/LibreOffice.
- [ ] Mock smoke run exits 0.
- [ ] Copied gold/mock outputs earn the intended score.
- [ ] Report explains any optional skipped rendered/judge checks clearly.
- [ ] `review/index.html` includes seed, outputs, and gold comparison targets.
- [ ] Final turn has at least one preservation/collateral-damage check.
- [ ] Instructions and checks agree; no hidden requirement exists only in the gold file.
- [ ] The task can be understood by someone who only reads the manifest and opens the artifacts.

## Common fixes

### `package artifact ... is missing`

The path in `artifacts.package` is relative to the task directory. Create the file or remove the declaration.

### `unknown evaluator`

Use only evaluator names listed in this guide, or add the evaluator implementation and schema entry first.

### `check ... references unknown artifact namespace`

Check refs must be either `package.<artifact_id>` or `run.outputs.<turn_id>.<output_id>` and the corresponding artifact/output must be declared.

### Layout check fails on a good deck

Make the region broader, increase `tolerance`, or select by a more stable text string/shape name.

### Style check fails on a good deck

PowerPoint may split text into runs. Ensure the selected text has the target style on a non-empty run, and prefer exact RGB colors such as `#1F4E79`.

### Preservation check fails unexpectedly

If `compare: exact_slide_text` is too strict, protect only sentinel text with `protected_texts`, or use selector/tolerance preservation for a particular shape.

### VLM judge is skipped

Install/enable LibreOffice `soffice` for PNG rendering. With `openai-oauth`, also provide `--judge-image-url-base` that points to an HTTP(S)-served run directory.

## Recommended first 2--3 manual tasks

If you need a concrete first batch, make these:

1. `launch_readiness_deck` — PPTX, 3 slides, sketch-guided title/dashboard layout, final brand style, protected appendix slide.
2. `research_progress_briefing` — PPTX, 2--3 slides, source bullets/data input, final visual hierarchy update, protected methods slide text.
3. `sales_pipeline_summary` — PPTX, 3 slides, small XLSX/JSON/TXT source data as input context, final metric update, preservation of speaker-ready summary wording.

Each should use the same package skeleton and smoke workflow above. Vary the required content, protected slide, and layout/style checks so the reports demonstrate multiple CUIF evaluation dimensions.
