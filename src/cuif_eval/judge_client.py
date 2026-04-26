from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class JudgeClientError(RuntimeError):
    pass


class JudgeClient:
    def __init__(self, *, base_url: str, model: str, api_key_env: str = "OPENAI_API_KEY", cache_dir: str | Path | None = None, refresh_cache: bool = False) -> None:
        if not base_url:
            raise JudgeClientError("judge base URL is required for live judge mode")
        if not model:
            raise JudgeClientError("judge model is required for live judge mode")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.refresh_cache = refresh_cache
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_key(self, *, prompt: str, rubric: str, artifacts: list[str | Path]) -> str:
        payload = {
            "base_url": self.base_url,
            "model": self.model,
            "prompt": prompt,
            "rubric": rubric,
            "artifacts": [{"path": str(path), "sha256": sha256_file(path)} for path in artifacts],
        }
        blob = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def evaluate(self, *, prompt: str, rubric: str, artifacts: list[str | Path]) -> dict[str, Any]:
        key = self.cache_key(prompt=prompt, rubric=rubric, artifacts=artifacts)
        cache_path = self.cache_dir / f"{key}.json" if self.cache_dir is not None else None
        if cache_path is not None and cache_path.exists() and not self.refresh_cache:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["cache"] = {"hit": True, "key": key, "path": str(cache_path)}
            return cached

        messages = [
            {"role": "system", "content": "You are a strict office-artifact evaluator. Return JSON with pass, score, and rationale."},
            {"role": "user", "content": f"Prompt:\n{prompt}\n\nRubric:\n{rubric}\n\nArtifacts:\n" + "\n".join(str(p) for p in artifacts)},
        ]
        request_payload = {"model": self.model, "messages": messages, "temperature": 0}
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get(self.api_key_env)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(request_payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - user-configured local endpoint
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise JudgeClientError(f"judge request failed: {exc}") from exc

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = self.parse_response(content)
        result = {"request": {"endpoint": "/chat/completions", "model": self.model}, "raw_response": data, "parsed": parsed, "cache": {"hit": False, "key": key}}
        if cache_path is not None:
            cache_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
            result["cache"]["path"] = str(cache_path)
        return result

    @staticmethod
    def parse_response(content: str) -> dict[str, Any]:
        try:
            parsed = json.loads(content)
            return {
                "pass": bool(parsed.get("pass", parsed.get("passes", False))),
                "score": float(parsed.get("score", 1.0 if parsed.get("pass") else 0.0)),
                "rationale": str(parsed.get("rationale", parsed.get("reason", ""))),
            }
        except Exception:
            lowered = content.lower()
            return {"pass": "pass" in lowered and "fail" not in lowered, "score": 1.0 if "pass" in lowered and "fail" not in lowered else 0.0, "rationale": content}
