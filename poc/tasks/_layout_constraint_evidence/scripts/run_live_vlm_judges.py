from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from cuif_eval.judge_client import JudgeClient

ROOT = Path(__file__).resolve().parents[4]
TASKS = [
    "annotated_layout_repair_deck",
    "public_template_compliance_deck",
    "native_chart_style_deck",
]
TASK_DIR = ROOT / "poc" / "tasks"
EVIDENCE = TASK_DIR / "_layout_constraint_evidence" / "ralph_completion" / "live_judge"
OPENAI_PORT = int(os.environ.get("CUIF_RALPH_OAUTH_PORT", "10561"))
BASE_URL = f"http://127.0.0.1:{OPENAI_PORT}/v1"
MODEL = "gpt-5.4"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class Proc:
    def __init__(self, proc: subprocess.Popen[str], log_path: Path):
        self.proc = proc
        self.log_path = log_path

    def terminate(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def wait_http(url: str, timeout: float = 45) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310 local/public test endpoint
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(1)
    return False


def start_oauth() -> Proc:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    log = EVIDENCE / f"openai_oauth_{now()}.log"
    handle = log.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        ["npx", "-y", "openai-oauth", "--host", "127.0.0.1", "--port", str(OPENAI_PORT), "--models", MODEL],
        cwd=ROOT,
        text=True,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )
    if not wait_http(f"{BASE_URL}/models", timeout=60):
        proc.terminate()
        raise RuntimeError(f"openai-oauth did not become ready; see {log}")
    return Proc(proc, log)


def start_http(directory: Path, port: int, label: str) -> Proc:
    directory.mkdir(parents=True, exist_ok=True)
    log = EVIDENCE / f"{label}_http_{now()}.log"
    handle = log.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(directory)],
        cwd=ROOT,
        text=True,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )
    if not wait_http(f"http://127.0.0.1:{port}/", timeout=20):
        proc.terminate()
        raise RuntimeError(f"http server did not become ready; see {log}")
    return Proc(proc, log)


def start_tunnel(port: int, label: str) -> tuple[Proc, str]:
    log = EVIDENCE / f"{label}_localtunnel_{now()}.log"
    handle = log.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        ["npx", "-y", "localtunnel", "--port", str(port), "--local-host", "127.0.0.1"],
        cwd=ROOT,
        text=True,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 45
    url = ""
    while time.monotonic() < deadline:
        if log.exists():
            text = log.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"https://[^\s]+", text)
            if match:
                url = match.group(0).rstrip("/")
                break
        if proc.poll() is not None:
            raise RuntimeError(f"localtunnel exited early; see {log}")
        time.sleep(1)
    if not url:
        proc.terminate()
        raise RuntimeError(f"localtunnel did not report a public URL; see {log}")
    return Proc(proc, log), url


def run_cmd(command: list[str], log: Path, timeout: int = 900) -> int:
    with log.open("w", encoding="utf-8") as handle:
        handle.write("$ " + " ".join(command) + "\n")
        handle.flush()
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        handle.write(f"\nexit_code={completed.returncode}\n")
        return completed.returncode


def summarize_report(run_dir: Path) -> dict:
    report = run_dir / "report.json"
    results = run_dir / "evaluation_results.json"
    report_data = json.loads(report.read_text(encoding="utf-8"))
    result_data = json.loads(results.read_text(encoding="utf-8")) if results.exists() else []
    interesting = []
    for result in result_data:
        if result.get("evaluator") in {"vlm_layout_rubric", "llm_text_rubric"}:
            evidence = result.get("evidence", {})
            interesting.append(
                {
                    "check_id": result.get("check_id"),
                    "evaluator": result.get("evaluator"),
                    "status": result.get("status"),
                    "message": result.get("message"),
                    "image_urls": evidence.get("request", {}).get("image_urls") or evidence.get("image_urls"),
                }
            )
    return {"summary": report_data.get("summary"), "judge_checks": interesting, "report": str(report)}


def evaluate_manifest_judge(task_id: str, idx: int) -> dict:
    run_dir = ROOT / "output" / "runs" / f"ralph_{task_id}_judge_public"
    http = tunnel = None
    try:
        http = start_http(run_dir, 18860 + idx, f"{task_id}_run")
        tunnel, public_url = start_tunnel(18860 + idx, f"{task_id}_run")
        # Confirm the public tunnel reaches the run root before asking OpenAI to fetch previews.
        wait_http(public_url + "/", timeout=20)
        log = TASK_DIR / task_id / "evidence" / "live_judge_public_ralph.log"
        code = run_cmd(
            [
                "uv", "run", "cuif-eval", "run",
                "--task", f"poc/tasks/{task_id}",
                "--adapter", "mock",
                "--out", f"output/runs/ralph_{task_id}_judge_public",
                "--judge-base-url", BASE_URL,
                "--judge-model", MODEL,
                "--judge-image-url-base", public_url,
                "--refresh-judge-cache",
            ],
            log,
            timeout=900,
        )
        summary = summarize_report(run_dir)
        summary.update({"task_id": task_id, "exit_code": code, "public_url": public_url, "log": str(log)})
        return summary
    finally:
        if tunnel:
            tunnel.terminate()
        if http:
            http.terminate()


def direct_multimodal_asset_review(task_id: str, idx: int) -> dict:
    review_dir = TASK_DIR / task_id / "evidence" / "multimodal_review"
    image_names = ["input_assets_montage.png", "gold_turn1_montage.png", "gold_final_montage.png"]
    images = [review_dir / name for name in image_names]
    missing = [str(path) for path in images if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing multimodal review images for {task_id}: {missing}")
    http = tunnel = None
    try:
        http = start_http(review_dir, 18910 + idx, f"{task_id}_assets")
        tunnel, public_url = start_tunnel(18910 + idx, f"{task_id}_assets")
        image_urls = [f"{public_url}/{path.name}" for path in images]
        client = JudgeClient(base_url=BASE_URL, model=MODEL, cache_dir=review_dir / "judge_cache", refresh_cache=True)
        prompt = (
            f"Review the CUIF layout-constraint benchmark task `{task_id}` using these rendered/contact-sheet images. "
            "Check whether the visual inputs are concrete and whether the turn-1 and final gold decks visibly instantiate the referenced layout/style constraints. "
            "Return JSON with pass, score, and rationale."
        )
        rubric = (
            "Pass only if the input-assets montage contains concrete visual/layout/style constraints, the gold_turn1 montage follows them, "
            "the gold_final montage preserves/revises the layout as instructed, and there are no obvious overlaps or arbitrary styling contradictions."
        )
        result = client.evaluate(prompt=prompt, rubric=rubric, artifacts=[TASK_DIR / task_id / "manifest.yaml"], images=images, image_urls=image_urls)
        out = TASK_DIR / task_id / "evidence" / "vlm_gold_asset_review_ralph.json"
        out.write_text(json.dumps({"task_id": task_id, "public_url": public_url, "image_urls": image_urls, "result": result}, indent=2, sort_keys=True), encoding="utf-8")
        return {"task_id": task_id, "review": str(out), "parsed": result.get("parsed"), "image_urls": image_urls}
    finally:
        if tunnel:
            tunnel.terminate()
        if http:
            http.terminate()


def main() -> None:
    task_ids = sys.argv[1:] or TASKS
    oauth = start_oauth()
    manifest_results = []
    asset_results = []
    try:
        for idx, task_id in enumerate(task_ids):
            manifest_results.append(evaluate_manifest_judge(task_id, idx))
            asset_results.append(direct_multimodal_asset_review(task_id, idx))
    finally:
        oauth.terminate()
    summary = {
        "base_url": BASE_URL,
        "model": MODEL,
        "openai_oauth_log": str(oauth.log_path),
        "manifest_judge_results": manifest_results,
        "asset_review_results": asset_results,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    out = EVIDENCE / f"live_vlm_summary_{now()}.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
