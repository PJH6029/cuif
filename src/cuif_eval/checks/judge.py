from __future__ import annotations

from ..artifacts import resolve_artifact_ref
from ..judge_client import JudgeClient, JudgeClientError
from ..types import CheckResult, CheckSpec, Manifest, TurnSpec
from .core import make_result


def judge_rubric(spec: CheckSpec, turn: TurnSpec, manifest: Manifest, workspace, context: dict) -> CheckResult:
    if context.get("skip_judges"):
        return make_result(spec, turn, "skipped", evidence={"skip_judges": True}, message="Judge checks skipped by configuration")
    path = resolve_artifact_ref(manifest, workspace, spec.artifact)
    params = spec.params
    base_url = params.get("base_url") or context.get("judge_base_url") or manifest.judge.get("base_url")
    model = params.get("model") or context.get("judge_model") or manifest.judge.get("model")
    api_key_env = params.get("api_key_env") or context.get("judge_api_key_env") or manifest.judge.get("api_key_env") or "OPENAI_API_KEY"
    if not base_url or not model:
        return make_result(spec, turn, "error", evidence={"base_url": bool(base_url), "model": bool(model)}, message="Judge live mode requires base URL and model")
    try:
        client = JudgeClient(base_url=str(base_url), model=str(model), api_key_env=str(api_key_env), cache_dir=workspace.judge_cache_dir, refresh_cache=bool(context.get("refresh_judge_cache", False)))
        judge_result = client.evaluate(prompt=str(params.get("prompt", "")), rubric=str(params.get("rubric", "")), artifacts=[path])
    except JudgeClientError as exc:
        return make_result(spec, turn, "error", evidence={"error": str(exc)}, message=str(exc))
    parsed = judge_result.get("parsed", {})
    passed = bool(parsed.get("pass"))
    score = max(0.0, min(1.0, float(parsed.get("score", 1.0 if passed else 0.0))))
    result = make_result(spec, turn, "pass" if passed else "fail", earned=spec.points * score, evidence=judge_result, message=str(parsed.get("rationale", "Judge returned no rationale")))
    if passed:
        result.earned_points = spec.points * score
    return result
