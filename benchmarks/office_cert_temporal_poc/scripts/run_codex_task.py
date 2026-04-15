from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path

from common import ROOT, WORKSPACES, now_utc, read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--model")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--codex-bin", default="codex")
    args = parser.parse_args()

    workspace = WORKSPACES / args.task
    prompt = workspace / "TASK_PROMPT.md"
    metadata_path = workspace / "TASK_METADATA.json"
    if not prompt.exists():
        raise SystemExit(f"Missing prepared task prompt: {prompt}")
    if not metadata_path.exists():
        raise SystemExit(f"Missing task metadata: {metadata_path}")

    run_dir = workspace / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "codex_events.jsonl"
    stderr_path = run_dir / "codex_stderr.log"
    final_path = run_dir / "final_message.md"

    command = [
        args.codex_bin,
        "exec",
        "--full-auto",
        "--json",
        "--output-last-message",
        str(final_path),
        "-C",
        str(workspace),
    ]
    if args.model:
        command.extend(["--model", args.model])
    command.append("-")

    command_record = {
        "generated_at": now_utc(),
        "task": args.task,
        "workspace": str(workspace.relative_to(ROOT)),
        "command": command,
        "dry_run": args.dry_run,
    }
    write_json(run_dir / "command.json", command_record)

    if args.dry_run:
        print(" ".join(command))
        return 0

    start = time.time()
    with prompt.open("rb") as stdin, stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        proc = subprocess.Popen(
            command,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            proc.wait(timeout=args.timeout_seconds)
            result = {
                "task": args.task,
                "started_at": command_record["generated_at"],
                "finished_at": now_utc(),
                "duration_seconds": round(time.time() - start, 2),
                "returncode": proc.returncode,
                "stdout": str(stdout_path.relative_to(ROOT)),
                "stderr": str(stderr_path.relative_to(ROOT)),
                "final_message": str(final_path.relative_to(ROOT)),
            }
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=10)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=10)
            result = {
                "task": args.task,
                "started_at": command_record["generated_at"],
                "finished_at": now_utc(),
                "duration_seconds": round(time.time() - start, 2),
                "returncode": "timeout",
                "timeout_seconds": args.timeout_seconds,
                "stdout": str(stdout_path.relative_to(ROOT)),
                "stderr": str(stderr_path.relative_to(ROOT)),
                "final_message": str(final_path.relative_to(ROOT)),
            }
    write_json(run_dir / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
