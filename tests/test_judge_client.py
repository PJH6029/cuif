from __future__ import annotations

import json

from cuif_eval.judge_client import JudgeClient
from cuif_eval.runner import run_task


def test_skip_judges_returns_skipped_without_network(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True)
    judge = [r for r in result["results"] if r.evaluator == "llm_text_rubric"][0]
    assert judge.status == "skipped"
    assert judge.evidence["skip_judges"] is True


def test_cache_key_includes_endpoint_model_prompt_rubric_and_digest(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("hello", encoding="utf-8")
    a = JudgeClient(base_url="http://localhost:1/v1", model="m1", cache_dir=tmp_path)
    b = JudgeClient(base_url="http://localhost:2/v1", model="m1", cache_dir=tmp_path)
    c = JudgeClient(base_url="http://localhost:1/v1", model="m2", cache_dir=tmp_path)
    key = a.cache_key(prompt="p", rubric="r", artifacts=[artifact])
    assert key != b.cache_key(prompt="p", rubric="r", artifacts=[artifact])
    assert key != c.cache_key(prompt="p", rubric="r", artifacts=[artifact])
    artifact.write_text("changed", encoding="utf-8")
    assert key != a.cache_key(prompt="p", rubric="r", artifacts=[artifact])


def test_cached_response_reused_without_network(tmp_path, monkeypatch):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("hello", encoding="utf-8")
    client = JudgeClient(base_url="http://localhost:1/v1", model="m1", cache_dir=tmp_path)
    key = client.cache_key(prompt="p", rubric="r", artifacts=[artifact])
    cache_path = tmp_path / f"{key}.json"
    cache_path.write_text(json.dumps({"parsed": {"pass": True, "score": 1, "rationale": "cached"}}), encoding="utf-8")
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network called")))
    result = client.evaluate(prompt="p", rubric="r", artifacts=[artifact])
    assert result["cache"]["hit"] is True
    assert result["parsed"]["rationale"] == "cached"


def test_refresh_bypasses_cache_and_request_shape_targets_chat_completions(tmp_path, monkeypatch):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("hello", encoding="utf-8")
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def read(self):
            return json.dumps({"choices": [{"message": {"content": json.dumps({"pass": True, "score": 0.5, "rationale": "ok"})}}]}).encode()

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = JudgeClient(base_url="http://localhost:9999/v1", model="m1", cache_dir=tmp_path, refresh_cache=True)
    result = client.evaluate(prompt="p", rubric="r", artifacts=[artifact])
    assert seen["url"].endswith("/chat/completions")
    assert seen["body"]["model"] == "m1"
    assert result["parsed"]["score"] == 0.5
