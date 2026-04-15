# Repo-Local HWP MCP Setup

`jkf87/hwp-mcp` controls Hancom HWP through Windows COM automation. It is not a
Linux HWP parser. Native HWP benchmark execution therefore needs:

- Windows
- Hancom HWP installed and licensed
- Python 3.7+
- Codex CLI

## Install Locally

Run from the repository root on the Windows/HWP machine:

```powershell
uv run --project benchmarks/office_cert_temporal_poc `
  python benchmarks/office_cert_temporal_poc/scripts/install_hwp_mcp.py --install
```

This installs the MCP checkout under the ignored path:

```text
benchmarks/office_cert_temporal_poc/.tools/hwp-mcp/
```

The helper also writes:

```text
benchmarks/office_cert_temporal_poc/.tools/hwp-mcp/codex_mcp_add.ps1
```

Run that generated command, or register manually:

```powershell
codex mcp add hwp -- `
  <repo>\benchmarks\office_cert_temporal_poc\.tools\hwp-mcp\.venv\Scripts\python.exe `
  <repo>\benchmarks\office_cert_temporal_poc\.tools\hwp-mcp\hwp_mcp_stdio_server.py
```

## Smoke Test

After registration:

```powershell
codex mcp list
codex exec -C <repo> "Use the hwp MCP ping-pong tool with message 핑 and report the result."
```

For a real HWP task, prepare the task workspace and run:

```powershell
uv run --project benchmarks/office_cert_temporal_poc `
  python benchmarks/office_cert_temporal_poc/scripts/prepare_tasks.py --task itq_latest_hwp

uv run --project benchmarks/office_cert_temporal_poc `
  python benchmarks/office_cert_temporal_poc/scripts/run_codex_task.py --task itq_latest_hwp
```

If HWP opens security dialogs for file access, use the security module included
with `hwp-mcp` or handle the dialogs manually during the PoC run.
