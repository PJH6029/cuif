from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..artifacts import resolve_artifact_ref
from ..judge_client import JudgeClient, JudgeClientError
from ..pptx.extract import summarize_pptx
from ..pptx.render import render_pptx_previews
from ..types import CheckResult, CheckSpec, Manifest, TurnSpec
from .core import make_result


def _artifact_summary(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".pptx":
        return summarize_pptx(path)
    return {"path": str(path), "size_bytes": path.stat().st_size if path.exists() else None}


def _image_urls(images: list[str], *, workspace, image_url_base: str | None) -> list[str]:
    if not image_url_base:
        return []
    urls: list[str] = []
    for image in images:
        image_path = Path(image)
        try:
            relative = image_path.resolve().relative_to(workspace.run_dir.resolve()).as_posix()
        except ValueError:
            relative = image_path.name
        urls.append(f"{image_url_base.rstrip('/')}/{relative}")
    return urls


def _judge_client(workspace, base_url: str, model: str, api_key_env: str, context: dict) -> JudgeClient:
    return JudgeClient(
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        cache_dir=workspace.judge_cache_dir,
        refresh_cache=bool(context.get("refresh_judge_cache", False)),
    )


def judge_rubric(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict) -> CheckResult:
    if context.get("skip_judges"):
        return make_result(spec, turn, "skipped", evidence={"skip_judges": True}, message="Judge checks skipped by configuration")
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    params = spec.params
    artifact_summary = _artifact_summary(path)
    rendered_preview = None
    images = []
    if spec.evaluator == "vlm_layout_rubric":
        rendered_preview = render_pptx_previews(path, workspace.previews_dir, f"judge_{turn.id}_{spec.id}")
        images = rendered_preview.get("images", [])
        if not images:
            status = "skipped" if spec.optional else "blocked"
            return make_result(
                spec,
                turn,
                status,
                evidence={"rendered_preview": rendered_preview},
                message=rendered_preview.get("message", "VLM judge requires rendered PNG previews, but none were produced."),
            )
    base_url = params.get("base_url") or context.get("judge_base_url") or manifest.judge.get("base_url")
    model = params.get("model") or context.get("judge_model") or manifest.judge.get("model")
    api_key_env = params.get("api_key_env") or context.get("judge_api_key_env") or manifest.judge.get("api_key_env") or "OPENAI_API_KEY"
    image_url_base = params.get("image_url_base") or context.get("judge_image_url_base") or manifest.judge.get("image_url_base")
    image_urls = _image_urls(images, workspace=workspace, image_url_base=str(image_url_base) if image_url_base else None)
    if not base_url or not model:
        return make_result(
            spec,
            turn,
            "error",
            evidence={"base_url": bool(base_url), "model": bool(model)},
            message="Judge live mode requires base URL and model",
        )
    try:
        client = _judge_client(workspace, str(base_url), str(model), str(api_key_env), context)
        prompt = str(params.get("prompt", ""))
        prompt += "\n\nStructured artifact summary available to the judge:\n"
        prompt += json.dumps(artifact_summary, indent=2, sort_keys=True)
        judge_result = client.evaluate(
            prompt=prompt,
            rubric=str(params.get("rubric", "")),
            artifacts=[path],
            images=images,
            image_urls=image_urls,
        )
    except JudgeClientError as exc:
        return make_result(
            spec,
            turn,
            "error",
            evidence={
                "error": str(exc),
                "artifact_summary": artifact_summary,
                "rendered_preview": rendered_preview,
                "image_urls": image_urls,
            },
            message=str(exc),
        )
    judge_result["artifact_summary"] = artifact_summary
    if rendered_preview is not None:
        judge_result["rendered_preview"] = rendered_preview
    parsed = judge_result.get("parsed", {})
    passed = bool(parsed.get("pass"))
    score = max(0.0, min(1.0, float(parsed.get("score", 1.0 if passed else 0.0))))
    result = make_result(
        spec,
        turn,
        "pass" if passed else "fail",
        earned=spec.points * score,
        evidence=judge_result,
        message=str(parsed.get("rationale", "Judge returned no rationale")),
    )
    if passed:
        result.earned_points = spec.points * score
    return result
