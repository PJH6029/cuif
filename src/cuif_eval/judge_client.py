from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
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


def image_data_url(path: str | Path) -> str:
    path = Path(path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


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

    def cache_key(
        self,
        *,
        prompt: str,
        rubric: str,
        artifacts: list[str | Path],
        images: list[str | Path] | None = None,
        image_urls: list[str] | None = None,
    ) -> str:
        payload = {
            "base_url": self.base_url,
            "model": self.model,
            "prompt": prompt,
            "rubric": rubric,
            "artifacts": [{"path": str(path), "sha256": sha256_file(path)} for path in artifacts],
            "images": [{"path": str(path), "sha256": sha256_file(path)} for path in images or []],
            "image_urls": image_urls or [],
        }
        blob = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def evaluate(
        self,
        *,
        prompt: str,
        rubric: str,
        artifacts: list[str | Path],
        images: list[str | Path] | None = None,
        image_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        images = images or []
        image_urls = image_urls or []
        if image_urls and len(image_urls) != len(images):
            raise JudgeClientError("image_urls length must match images length")
        key = self.cache_key(prompt=prompt, rubric=rubric, artifacts=artifacts, images=images, image_urls=image_urls)
        cache_path = self.cache_dir / f"{key}.json" if self.cache_dir is not None else None
        if cache_path is not None and cache_path.exists() and not self.refresh_cache:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["cache"] = {"hit": True, "key": key, "path": str(cache_path)}
            return cached

        user_text = f"Prompt:\n{prompt}\n\nRubric:\n{rubric}\n\nArtifacts:\n" + "\n".join(str(p) for p in artifacts)
        if images:
            user_content: str | list[dict[str, Any]] = [{"type": "text", "text": user_text}]
            for idx, image_path in enumerate(images):
                url = image_urls[idx] if image_urls else image_data_url(image_path)
                user_content.append({"type": "image_url", "image_url": {"url": url}})
        else:
            user_content = user_text
        messages = [
            {"role": "system", "content": "You are a strict office-artifact evaluator. Return JSON with pass, score, and rationale."},
            {"role": "user", "content": user_content},
        ]
        request_payload = {"model": self.model, "messages": messages}
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
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:2000]
            raise JudgeClientError(f"judge request failed: HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise JudgeClientError(f"judge request failed: {exc}") from exc

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = self.parse_response(content)
        result = {
            "request": {
                "endpoint": "/chat/completions",
                "model": self.model,
                "artifact_paths": [str(path) for path in artifacts],
                "image_paths": [str(path) for path in images],
                "image_urls": image_urls,
                "image_count": len(images),
            },
            "raw_response": data,
            "parsed": parsed,
            "cache": {"hit": False, "key": key},
        }
        if cache_path is not None:
            cache_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
            result["cache"]["path"] = str(cache_path)
        return result

    @staticmethod
    def parse_response(content: str) -> dict[str, Any]:
        candidate = content.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`").strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
        try:
            parsed = json.loads(candidate)
            return {
                "pass": bool(parsed.get("pass", parsed.get("passes", False))),
                "score": float(parsed.get("score", 1.0 if parsed.get("pass") else 0.0)),
                "rationale": str(parsed.get("rationale", parsed.get("reason", ""))),
            }
        except Exception:
            lowered = content.lower()
            return {"pass": "pass" in lowered and "fail" not in lowered, "score": 1.0 if "pass" in lowered and "fail" not in lowered else 0.0, "rationale": content}
