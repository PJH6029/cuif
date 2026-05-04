from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASKS = [
    "annotated_layout_repair_deck",
    "public_template_compliance_deck",
    "native_chart_style_deck",
]
MODEL = "gpt-5.3-codex-spark"
TIMEOUT = 1800
PROMPT = (
    "Work only in this directory. Follow instruction.md exactly. "
    "Create an editable PowerPoint result, not a screenshot-only shortcut. "
    "Use the provided seed and inputs. Save the completed artifact exactly as {output_path}."
)


def run(command: list[str], log_path: Path, timeout: int = TIMEOUT) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        log.write("$ " + " ".join(command) + "\n")
        log.flush()
        try:
            completed = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
            code = completed.returncode
        except subprocess.TimeoutExpired:
            log.write(f"\nTIMEOUT after {timeout}s\n")
            code = 124
        log.write(f"\nexit_code={code}\n")
    return code


def summarize_report(report: Path) -> dict | None:
    if not report.exists():
        return None
    data = json.loads(report.read_text(encoding="utf-8"))
    return data.get("summary") or data.get("aggregate") or data


def task_result(task_id: str) -> dict:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    task_dir = f"poc/tasks/{task_id}"
    bundle = f"output/bundles/ralph_baseline/{task_id}_{stamp}"
    run_dir = f"output/runs/ralph_baseline/{task_id}_{stamp}"
    task_evidence = ROOT / "poc" / "tasks" / task_id / "evidence"
    log_path = task_evidence / f"codex_baseline_ralph_{stamp}.log"
    command = [
        "uv", "run", "cuif-eval", "run-and-evaluate",
        "--task", task_dir,
        "--bundle", bundle,
        "--run", run_dir,
        "--agent", "codex-exec",
        "--agent-arg=--model", f"--agent-arg={MODEL}",
        "--prompt-template", PROMPT,
        "--overwrite-bundle",
        "--skip-judges",
    ]
    code = run(command, log_path)
    report = ROOT / run_dir / "report.json"
    followup = None
    # If the outer wrapper timed out after the agent wrote outputs, import/evaluate
    # the bundle so timeout is not the terminal evidence state.
    if not report.exists():
        follow_log = task_evidence / f"codex_baseline_ralph_followup_eval_{stamp}.log"
        follow_run = f"output/runs/ralph_baseline/{task_id}_{stamp}_followup_eval"
        follow_code = run(
            [
                "uv", "run", "cuif-eval", "evaluate-bundle",
                "--task", task_dir,
                "--workspace", f"{bundle}/current",
                "--run", follow_run,
                "--skip-judges",
            ],
            follow_log,
            timeout=300,
        )
        follow_report = ROOT / follow_run / "report.json"
        followup = {"exit_code": follow_code, "log": str(follow_log.relative_to(ROOT)), "run_dir": follow_run, "report": str(follow_report.relative_to(ROOT)) if follow_report.exists() else None, "summary": summarize_report(follow_report)}
        if follow_report.exists():
            report = follow_report
            run_dir = follow_run
    return {
        "task_id": task_id,
        "model": MODEL,
        "exit_code": code,
        "log": str(log_path.relative_to(ROOT)),
        "bundle": bundle,
        "run_dir": run_dir,
        "report": str(report.relative_to(ROOT)) if report.exists() else None,
        "summary": summarize_report(report),
        "followup": followup,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    results = [task_result(task_id) for task_id in TASKS]
    out_dir = ROOT / "poc" / "tasks" / "_layout_constraint_evidence" / "ralph_completion" / "baselines"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"codex_baseline_summary_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps({"results": results}, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"summary_path": str(out.relative_to(ROOT)), "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
