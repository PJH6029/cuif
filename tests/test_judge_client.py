from __future__ import annotations

import json
import base64

from cuif_eval.judge_client import JudgeClient
from cuif_eval.runner import run_task

PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="


def write_tiny_png(path):
    path.write_bytes(base64.b64decode(PNG_1X1))


def fake_chat_response(rationale, score=1.0, passed=True):
    payload = {"pass": passed, "score": score, "rationale": rationale}
    return json.dumps({"choices": [{"message": {"content": json.dumps(payload)}}]}).encode()


def test_skip_judges_returns_skipped_without_network(toy_task, tmp_path):
    result = run_task(toy_task, adapter_name="mock", out=tmp_path / "run", skip_judges=True)
    judges = [r for r in result["results"] if r.evaluator in {"llm_text_rubric", "vlm_layout_rubric"}]
    assert {judge.evaluator for judge in judges} == {"llm_text_rubric", "vlm_layout_rubric"}
    assert all(judge.status == "skipped" for judge in judges)
    assert all(judge.evidence["skip_judges"] is True for judge in judges)


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
    image = tmp_path / "image.png"
    write_tiny_png(image)
    assert key != a.cache_key(prompt="p", rubric="r", artifacts=[artifact], images=[image])


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
            return fake_chat_response("ok", score=0.5)

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


def test_vlm_request_shape_includes_png_image_url(tmp_path, monkeypatch):
    artifact = tmp_path / "artifact.pptx"
    artifact.write_bytes(b"pptx placeholder")
    image = tmp_path / "preview.png"
    write_tiny_png(image)
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def read(self):
            return fake_chat_response("vision ok")

    def fake_urlopen(request, timeout):
        seen["body"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = JudgeClient(base_url="http://localhost:9999/v1", model="vision-model", cache_dir=tmp_path)
    result = client.evaluate(prompt="p", rubric="r", artifacts=[artifact], images=[image])
    content = seen["body"]["messages"][1]["content"]
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert result["request"]["image_count"] == 1


def test_vlm_request_can_use_public_png_url_for_openai_oauth(tmp_path, monkeypatch):
    artifact = tmp_path / "artifact.pptx"
    artifact.write_bytes(b"pptx placeholder")
    image = tmp_path / "preview.png"
    write_tiny_png(image)
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def read(self):
            return fake_chat_response("url ok")

    def fake_urlopen(request, timeout):
        seen["body"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = JudgeClient(base_url="http://localhost:9999/v1", model="vision-model", cache_dir=tmp_path)
    result = client.evaluate(prompt="p", rubric="r", artifacts=[artifact], images=[image], image_urls=["https://example.test/preview.png"])
    image_url = seen["body"]["messages"][1]["content"][1]["image_url"]["url"]
    assert image_url == "https://example.test/preview.png"
    assert result["request"]["image_urls"] == ["https://example.test/preview.png"]


def test_vlm_judge_check_renders_png_and_calls_fake_openai_compatible_endpoint(toy_task, tmp_path, monkeypatch):
    seen_bodies = []

    def fake_render(path, previews_dir, label):
        image = previews_dir / label / "result.png"
        image.parent.mkdir(parents=True, exist_ok=True)
        write_tiny_png(image)
        return {
            "status": "rendered",
            "renderer": "fake",
            "summary": str(image.with_suffix(".json")),
            "html": str(image.with_suffix(".html")),
            "images": [str(image)],
        }

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def read(self):
            return fake_chat_response("judge ok")

    def fake_urlopen(request, timeout):
        seen_bodies.append(json.loads(request.data.decode()))
        return FakeResponse()

    monkeypatch.setattr("cuif_eval.checks.judge.render_pptx_previews", fake_render)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = run_task(
        toy_task,
        adapter_name="mock",
        out=tmp_path / "run",
        skip_judges=False,
        judge_base_url="http://localhost:9999/v1",
        judge_model="fake-judge",
        judge_image_url_base="https://example.test/run",
    )
    statuses = {r.check_id: r.status for r in result["results"]}
    assert statuses["optional_llm_summary_judge"] == "pass"
    assert statuses["optional_vlm_layout_judge"] == "pass"
    assert any(isinstance(body["messages"][1]["content"], list) for body in seen_bodies)
    image_bodies = [body for body in seen_bodies if isinstance(body["messages"][1]["content"], list)]
    assert image_bodies[0]["messages"][1]["content"][1]["image_url"]["url"].startswith("https://example.test/run/previews/")
