# Partial-credit, multi-turn, and multimodal evaluation patterns beyond office benchmarks

Office-family benchmarks rarely provide strong trajectory or multi-turn scoring. This file reviews broader agent benchmarks whose evaluation mechanisms can be imported into CUIF.

## Pattern matrix

| Benchmark | Domain | Multi-turn? | Multimodal? | Evaluation mechanism | What CUIF should borrow |
|---|---|---:|---:|---|---|
| [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) | Workplace/professional tasks | Yes, long agent workflows; multiple apps | Some tasks include office artifacts and VLM checks | Weighted checkpoints, deterministic + LLM/VLM evaluators, optional trajectory path for partial credit | Checkpoint schema, partial scores, office-like evaluator examples |
| [Mind2Web](https://github.com/OSU-NLP-Group/Mind2Web) / [Multimodal-Mind2Web](https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web) | Web action prediction | Recorded multi-step trajectories | Multimodal variant has screenshots | Element accuracy, action F1, step accuracy, macro per-task aggregation, error-ratio distribution | Per-step partial trajectory metrics and macro averaging |
| [VisualWebArena](https://github.com/web-arena-x/visualwebarena) | Visual web tasks | Multi-step agent trajectory, single task instruction | Yes: visual web observations, image tasks | String/URL/programmatic HTML checks plus image/VQA/SSIM checks; evaluator scores combined multiplicatively | Multimodal final checks and image-query evaluators |
| [WebArena](https://github.com/web-arena-x/webarena) | Web tasks | Multi-step agent trajectory | Mostly text/DOM screenshots depending agent | Final goal validators over web state/URL/content | Web-state evaluator modularity; less useful for partial credit |
| [WorkArena](https://github.com/ServiceNow/WorkArena) / [WorkArena++](https://arxiv.org/abs/2407.05291) | ServiceNow enterprise workflows | Compositional multi-step tasks | Browser UI | `task.validate(page, chat_messages)` returns reward/done/message/info; compositional tasks validate after subtasks in demos | Subtask decomposition and enterprise workflow realism |
| [AppWorld](https://github.com/stonybrooknlp/appworld) | Simulated apps/APIs | Multi-step API/code agents | No visual modality | Database-state unit tests; pass percentage and success if all tests pass; online evaluate | Unit-test-like partial scoring and collateral-damage checks |
| [tau2/tau3-bench](https://github.com/sierra-research/tau2-bench) | Customer-service tool-agent-user interaction | Yes: simulated user-agent conversations; text and voice | tau3 adds voice; knowledge domain | Environment DB checks, expected action checks, communication checks, optional NL assertions; component rewards multiplied; pass^k | Multi-turn user simulation and action/env/communication reward components |
| [AndroidWorld](https://github.com/google-research/android_world) | Android device control | Agent trajectories over emulator | Yes: mobile screenshots/UI | Per-task `is_successful(env)` durable reward validators; parameterized task instances | Dynamic task instantiation and robust state validators |
| [OSWorld](https://github.com/xlang-ai/OSWorld) | Desktop computer use | Multi-step GUI trajectory, single initial instruction | Yes: desktop screenshots/accessibility | Final-state evaluator functions over files/UI/images, combined via `and`/`or` | File-specific metrics and reproducible desktop harness |
| [WindowsAgentArena](https://github.com/microsoft/WindowsAgentArena) | Windows desktop | Multi-step GUI trajectory | Yes | OSWorld-style task JSON evaluators, scalable parallel Windows eval | Scalable real-OS infra and trajectory logging |

## TheAgentCompany

**Primary source:** [GitHub](https://github.com/TheAgentCompany/TheAgentCompany), [arXiv](https://arxiv.org/abs/2412.14161).  
**Audited clone:** `/tmp/cuif_lit_repos/TheAgentCompany` at `98b68ef`.

TheAgentCompany is the best audited example of practical task partial credit that includes office-like artifacts.

### Scope

The audited repo has 175 tasks distributed across workplace roles:

- SDE 69;
- HR 29;
- PM 28;
- admin 15;
- data science 14;
- finance 12;
- smaller QA/research/ML/example tasks.

Office-like examples include:

- `admin-make-spreadsheet`;
- `ds-format-excel-sheets`;
- `ds-stock-analysis-slides`;
- `hr-internal-tooling-slides`;
- `hr-create-employee-manual`;
- `hr-populate-salary-increase-memo`.

### Evaluation pipeline

Code paths:

- `workspaces/base_image/scoring.py`
- task-specific `/utils/eval.py` and evaluator modules in task images
- example task evaluators such as `admin-make-spreadsheet/evaluator.py`, `ds-stock-analysis-slides/evaluator.py`, `hr-internal-tooling-slides/evaluator.py`, `ds-format-excel-sheets/evaluator.py`

Evaluation model:

1. Each task has an encrypted evaluator in its Docker image. Agents cannot see rubrics/eval code.
2. The evaluator returns `Checkpoint(total, result)` objects.
3. `Result.final_score` sums checkpoint totals/results by default.
4. Optional strategies add bonuses for completing final/any/given checkpoints.
5. Evaluators may accept a `trajectory_path`; docs state it is often used to grant partial credits and should record all examinee steps.

Example evaluator patterns:

- `admin-make-spreadsheet`: four checkpoints totaling 5 points; one checkpoint can return 2/1/0 based on how many unique drinks were correctly captured.
- `ds-stock-analysis-slides`: CSV exact checks with pandas, PPTX chart/image checks with VLM, and script text LLM checks; total 8 points.
- `hr-internal-tooling-slides`: python-pptx plus LLM content checks, style/margins/no-markdown checks, and RocketChat message checks; total 10 points.
- `ds-format-excel-sheets`: openpyxl/pandas checks that original sheet is unchanged, copied formatted sheet is equal, required cell fill color is `#87CEEB`, and alignment is centered; total 4 points.

### CUIF import

Use TheAgentCompany’s checkpoint idea as the backbone, but specialize it to office artifacts:

```yaml
score:
  total: 20
  checkpoints:
    - id: turn1_table_created
      turn: 1
      points: 3
      evaluator: xlsx_table_shape
    - id: turn2_chart_matches_sketch
      turn: 2
      points: 4
      evaluator: rendered_vlm_region
    - id: no_collateral_slide_damage
      points: -3
      evaluator: pptx_non_target_diff
```

## Mind2Web and Multimodal-Mind2Web

**Primary source:** [Mind2Web GitHub](https://github.com/OSU-NLP-Group/Mind2Web), [arXiv](https://arxiv.org/abs/2306.06070), [Multimodal-Mind2Web dataset](https://huggingface.co/datasets/osunlp/Multimodal-Mind2Web).  
**Audited clone:** `/tmp/cuif_lit_repos/Mind2Web` at `33bd95c`.

Mind2Web contains more than 2,000 web tasks across 137 websites and 31 domains. It is valuable because it evaluates **step-level trajectories**, not just final success.

### Evaluation pipeline

Code path:

- `src/action_prediction/metric.py`

Metrics:

- `element_acc`: predicted target element matches a positive candidate by `backend_node_id`.
- `action_f1`: token F1 over predicted action string and target action, including action type (`CLICK`, `TYPE`, `SELECT`) and value.
- `step_acc`: 1 if both element accuracy and action F1 are perfect.
- Micro averages across all steps.
- Macro averages by `annotation_id`, so longer tasks do not dominate.
- `error_ratio`: distribution of failed-step counts per task.

### CUIF import

CUIF can define office trajectory leaves similarly:

- turn-level target object accuracy: selected slide/sheet/page/object is correct;
- operation type accuracy: insert/update/delete/style/chart/formula/export/send;
- argument F1/tolerance: text/value/style/layout arguments;
- per-turn success and macro task average;
- error-ratio distribution for how many turns/subgoals failed.

This is especially useful if CUIF collects/reference-generates expert trajectories.

## VisualWebArena

**Primary source:** [GitHub](https://github.com/web-arena-x/visualwebarena), [arXiv](https://arxiv.org/abs/2401.13649).  
**Audited clone:** `/tmp/cuif_lit_repos/VisualWebArena` at `89f5af2`.

VisualWebArena has 910 visual web tasks and supports screenshots/visual observations.

### Evaluation pipeline

Code path:

- `evaluation_harness/evaluators.py`

Evaluator types:

- `string_match`: exact/must-include/must-exclude/one-of/required numeric/fuzzy via LLM.
- `url_match`: exact or gold URL contained in prediction.
- `program_html`: navigate/query page DOM or helper functions, then run string/numeric/fuzzy checks.
- `page_image_query`: select images from page and evaluate via VQA/captioning or fuzzy image matching with SSIM.
- `EvaluatorComb`: multiplies component scores.

### CUIF import

The `page_image_query` pattern transfers well to rendered office pages/slides:

- crop chart/table/shape region;
- query VLM: “does the chart match the handwritten sketch?”;
- use image similarity when there is a pixel-level reference;
- combine with deterministic object checks.

## AppWorld

**Primary source:** [GitHub](https://github.com/stonybrooknlp/appworld), [arXiv](https://arxiv.org/abs/2407.18901).  
**Audited clone:** `/tmp/cuif_lit_repos/AppWorld` at `a072b7a`.

AppWorld is an interactive coding/API-agent benchmark over simulated apps. It is not multimodal, but it has excellent partial-credit and collateral-damage ideas.

### Evaluation pipeline

Code path:

- `src/appworld/evaluator.py`

The evaluator runs robust database-state unit tests:

- `TestTracker` tracks pass/fail cases;
- `pass_percentage = 100 * pass_count / num_tests`;
- `success` is true only when all tests pass;
- reports pass/fail details, requirements, labels, and stack traces;
- `world.evaluate()` can be called online at any point, enabling RL-style reward or per-step diagnostics.

### CUIF import

CUIF should treat artifact requirements like unit tests:

- deterministic leaf tests with clear error messages;
- pass percentage as partial score;
- explicit no-op/collateral tests;
- online evaluator mode for training agents, with hidden eval split for leaderboard.

## tau-bench / tau2 / tau3-bench

**Primary source:** [tau2/tau3-bench GitHub](https://github.com/sierra-research/tau2-bench), [tau-bench GitHub](https://github.com/sierra-research/tau-bench), [tau-bench arXiv](https://arxiv.org/abs/2406.12045).  
**Audited clones:** tau-bench `59a200c`, tau2/tau3 `ada8e51`.

The original tau-bench is a multi-turn tool-agent-user benchmark with an LLM user simulator. The current tau2/tau3 repo extends this to newer domains, voice/full-duplex, knowledge retrieval, and task fixes.

### Original tau-bench reward

Code path:

- `tau_bench/envs/base.py`

Reward is computed when the simulated user stops:

1. Compare the final database hash against a gold database produced by replaying expected tool actions.
2. Optionally check that required textual outputs appear in the agent’s responses.
3. Return binary reward 1/0.
4. Aggregate with `pass^k` over multiple trials.

### tau2/tau3 reward components

Code paths:

- `src/tau2/evaluator/evaluator.py`
- `src/tau2/evaluator/evaluator_env.py`
- `src/tau2/evaluator/evaluator_action.py`
- `src/tau2/evaluator/evaluator_communicate.py`
- `src/tau2/evaluator/evaluator_nl_assertions.py`
- `src/tau2/metrics/agent_metrics.py`

Evaluation types:

- `ENV`: database and environment assertions;
- `ACTION`: expected tool/action checks over the trajectory;
- `COMMUNICATE`: required communication checks;
- `NL_ASSERTIONS`: optional LLM-judged qualitative assertions;
- `ALL`: multiply applicable component rewards based on task reward basis;
- full-duplex variants evaluate tick-grouped audio/streaming trajectories.

Metrics include average reward, pass^k, action metrics, DB match counts, authentication status, termination reasons, responsiveness info for full-duplex mode, and LLM-judge review error stats.

### CUIF import

CUIF can mirror the reward-basis model:

- `ARTIFACT_STATE`: final PPTX/DOCX/XLSX properties;
- `TURN_STATE`: per-turn artifact states;
- `ACTION`: required/forbidden trajectory events;
- `COMMUNICATION`: correct clarification and user updates;
- `MULTIMODAL`: visual/sketch/template adherence;
- `QUALITY`: aesthetics/semantic writing quality.

## WorkArena / WorkArena++

**Primary source:** [GitHub](https://github.com/ServiceNow/WorkArena), [WorkArena arXiv](https://arxiv.org/abs/2403.07718), [WorkArena++ arXiv](https://arxiv.org/abs/2407.05291).  
**Audited clone:** `/tmp/cuif_lit_repos/WorkArena` at `a772230`.

WorkArena benchmarks enterprise ServiceNow workflows. WorkArena++ adds 682 compositional tasks. The core task interface validates through browser state:

- `task.validate(page, chat_messages)` returns reward/done/message/info.
- Cheat demos validate after each subtask, but aggregate benchmark scoring is mainly final binary reward.

### CUIF import

Useful for compositional task construction: combine atomic office operations into realistic workflows and validate subtask boundaries.

## OSWorld and WindowsAgentArena

Covered in detail in [`office_family_benchmarks.md`](office_family_benchmarks.md). They are relevant here because they evaluate multimodal GUI agents in real desktop environments, but their office tasks are mostly final-state checked.

### CUIF import

- use VM/containerized desktop state reset;
- log full trajectories/screenshots;
- export final artifacts for offline grading;
- reuse file metrics where possible;
- add CUIF-specific per-turn and rubric checks on top.

## AndroidWorld

**Primary source:** [GitHub](https://github.com/google-research/android_world), [paper](https://arxiv.org/pdf/2405.14573), [project page](https://google-research.github.io/android_world/).  
**Audited clone:** `/tmp/cuif_lit_repos/AndroidWorld` at `d9c569f`.

AndroidWorld has 116 hand-crafted Android tasks across 20 apps and dynamically instantiated parameters for many task variations. Evaluators are implemented as per-task `is_successful(env)` functions and common validators over app/device state.

### CUIF import

The dynamic instantiation pattern is useful:

- parameterize source data, names, colors, dates, amounts;
- generate many variants from seed office workflows;
- use durable validators rather than exact brittle outputs;
- expose millions of possible train variants while holding out template families for evaluation.

## Practical CUIF scoring design synthesized from these patterns

### Suggested task schema

```yaml
id: pptx_budget_review_001
family: pptx_xlsx_crossfile
turns:
  - user: "Use the spreadsheet to add a Q2 margin chart to slide 5. Match this sketch."
    inputs:
      - type: xlsx
        path: inputs/q2_financials.xlsx
      - type: pptx
        path: inputs/board_template.pptx
      - type: image
        path: inputs/handwritten_chart_layout.png
    expected:
      artifact_snapshot: gold/turn1.pptx
      checks:
        - id: chart_data_correct
          evaluator: ppt_chart_data
          points: 3
        - id: chart_matches_sketch
          evaluator: rendered_vlm_region
          points: 3
        - id: template_preserved
          evaluator: pptx_non_target_diff
          points: 2
  - user: "Actually make it brand blue and add a one-sentence insight under the chart."
    expected:
      artifact_snapshot: gold/final.pptx
      checks:
        - id: brand_color
          evaluator: ppt_style_color
          points: 2
        - id: insight_semantic
          evaluator: llm_text_rubric
          points: 2
score:
  aggregation: weighted_sum
  penalties:
    - id: collateral_damage
      evaluator: deck_wide_diff_penalty
      max_penalty: 4
```

### Suggested metric bundle

- `final_score`: weighted score / total points.
- `turn_score`: average per-turn score.
- `artifact_score`: deterministic file-state checks.
- `visual_score`: VLM/image checks.
- `trajectory_score`: action/step/communication checks when available.
- `collateral_penalty`: points lost for unintended edits.
- `success@threshold`: success at 80% or 90% partial score.
- `pass^k`: if multiple trials are run.
- `cost/actions/time`: efficiency metrics.

### Avoid these pitfalls

- Do not use only final binary success; it will hide meaningful partial progress.
- Do not use only LLM-as-judge; it will be noisy and hard to reproduce.
- Do not require exact PPTX binary equality; Office files often reorder XML or embed metadata.
- Do not overfit to one interface; support GUI, code, and OOXML/file agents.
- Do not ignore collateral damage; office editing agents often accidentally modify non-target content.
- Do not make every task open-ended; mix exact deterministic tasks, semi-open design tasks, and creative tasks with rubrics.
