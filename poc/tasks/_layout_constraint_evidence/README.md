# Layout-constraint rerun evidence

This directory stores repo-level evidence from the layout-constraint rerun so
`poc/` stays reserved for stable PoC docs and `poc/tasks/` contains task-facing
packages plus their associated review evidence.

## Contents

- `summaries/` — human-readable synthesis notes for multimodal review, task
  evidence, and worker-4 baseline/live-judge evidence.
- `multimodal_review/` — cross-task contact sheet, `openai-oauth` server logs,
  VLM probe responses, and curl stderr from the mandatory multimodal review.
- `verification/final/` — final integration gate log and summary.
- `verification/multimodal_review/` — worker-3 validation/mock/pytest logs for
  the multimodal review lane.
- `verification/task7/` — leader task-7 pytest evidence after the Task A visual
  fix.
- `worker_logs/` — worker-1 root-level logs that are shared across multiple task
  packages.

Package-local evidence remains inside each task directory under
`poc/tasks/<task_id>/evidence/`.
