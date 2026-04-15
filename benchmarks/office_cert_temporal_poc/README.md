# Office Certification Temporal Benchmark PoC

This directory contains a small proof of concept for using office certification
practice/exam materials as temporal CUIF benchmark inputs.

The PoC intentionally separates tracked benchmark metadata from local raw
materials:

- Tracked: source manifests, task manifests, prompts, scripts, setup notes, and
  summarized run metadata.
- Ignored: downloaded ZIP/PDF/XLSX/XLSM/PPTX/DOCX/HWP files, unpacked packages,
  Codex solver workspaces, rendered previews, and repo-local MCP checkouts.

## Source Policy

The selected source policy is "official plus free third-party":

- Official public sources are preferred.
- Free third-party practice examples may be used for PoC only, with source and
  license notes captured in metadata.
- Paid materials, credentialed dumps, and unauthorized MOS exam dumps are
  excluded.
- KPC ITQ materials must keep the KPC copyright/reuse warning attached in
  metadata. KPC states that ITQ/GTQ/ERP publicly expose only recent regular
  sessions and warns against unauthorized redistribution.

## Layout

- `sources.yml`: source definitions and download/discovery rules.
- `task_manifest.yml`: selected PoC tasks and solver profiles.
- `scripts/fetch_sources.py`: downloads or records source metadata.
- `scripts/prepare_tasks.py`: unpacks sources and creates gold-free solver
  workspaces.
- `scripts/run_codex_task.py`: opens one non-interactive Codex session for a
  prepared task.
- `scripts/inspect_artifacts.py`: lightweight checks for generated artifacts.
- `scripts/install_hwp_mcp.py`: repo-local HWP MCP setup helper.
- `docs/hwp_mcp_setup.md`: Windows/Hancom HWP setup guide.

## Quick Start

Run from the repository root.

```bash
uv run --project benchmarks/office_cert_temporal_poc \
  python benchmarks/office_cert_temporal_poc/scripts/fetch_sources.py --dry-run

uv run --project benchmarks/office_cert_temporal_poc \
  python benchmarks/office_cert_temporal_poc/scripts/fetch_sources.py --suite computer_skills_1

uv run --project benchmarks/office_cert_temporal_poc \
  python benchmarks/office_cert_temporal_poc/scripts/fetch_sources.py --suite itq

uv run --project benchmarks/office_cert_temporal_poc \
  python benchmarks/office_cert_temporal_poc/scripts/prepare_tasks.py --task cs1_excel_a

uv run --project benchmarks/office_cert_temporal_poc \
  python benchmarks/office_cert_temporal_poc/scripts/run_codex_task.py --task cs1_excel_a
```

MOS downloads are metadata-only by default because Microsoft Learn points to
large course packages and the page may require authorization in some tenants.
Use `--suite mos --include-large` only when the access and storage policy is
acceptable.

## HWP Requirement

HWP-native tasks require Windows, Hancom HWP, Python, and `hwp-mcp`. This Linux
workspace can prepare task metadata and repo-local setup files, but actual HWP
automation is expected to run on a Windows machine with HWP installed.

See `docs/hwp_mcp_setup.md`.

## Output Conventions

The task preparer creates ignored workspaces under:

```text
benchmarks/office_cert_temporal_poc/runs/workspaces/<task_id>/
```

Each solver workspace contains:

- problem/input files only
- `TASK_PROMPT.md`
- `outputs/` for generated artifacts
- `run/` for Codex logs and final messages

Gold/answer files stay in ignored cache directories outside the solver
workspace.
