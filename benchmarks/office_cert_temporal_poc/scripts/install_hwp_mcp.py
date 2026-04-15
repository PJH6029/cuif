from __future__ import annotations

import argparse
import os
import platform
import subprocess
from pathlib import Path

from common import ROOT, write_text


HWP_MCP_REPO = "https://github.com/jkf87/hwp-mcp.git"
TOOLS_DIR = ROOT / ".tools"
HWP_DIR = TOOLS_DIR / "hwp-mcp"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def write_codex_registration_files() -> None:
    if os.name == "nt":
        python_path = HWP_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        python_path = HWP_DIR / ".venv" / "bin" / "python"
    server_path = HWP_DIR / "hwp_mcp_stdio_server.py"

    ps = f"""codex mcp add hwp -- "{python_path}" "{server_path}"
"""
    sh = f"""#!/usr/bin/env bash
set -euo pipefail
codex mcp add hwp -- "{python_path}" "{server_path}"
"""
    write_text(HWP_DIR / "codex_mcp_add.ps1", ps)
    write_text(HWP_DIR / "codex_mcp_add.sh", sh)
    (HWP_DIR / "codex_mcp_add.sh").chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="Create venv and install dependencies.")
    parser.add_argument("--force-clone", action="store_true")
    parser.add_argument("--force-non-windows-install", action="store_true")
    args = parser.parse_args()

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if HWP_DIR.exists() and args.force_clone:
        raise SystemExit(f"Refusing to delete existing checkout automatically: {HWP_DIR}")
    if not HWP_DIR.exists():
        run(["git", "clone", HWP_MCP_REPO, str(HWP_DIR)])
    else:
        print(f"Using existing checkout: {HWP_DIR}")

    if args.install:
        if platform.system() != "Windows" and not args.force_non_windows_install:
            print("Skipping dependency install: hwp-mcp requires Windows + Hancom HWP + pywin32.")
            print("Run this script with --install on the Windows/HWP machine.")
        else:
            run(["uv", "venv", str(HWP_DIR / ".venv")])
            pip = HWP_DIR / ".venv" / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
            run([str(pip), "install", "-r", "requirements.txt"], cwd=HWP_DIR)
            run([str(pip), "install", "mcp"], cwd=HWP_DIR)

    write_codex_registration_files()
    print(f"HWP MCP checkout ready at {HWP_DIR}")
    print(f"Registration helper: {HWP_DIR / 'codex_mcp_add.ps1'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
