from __future__ import annotations

from pathlib import Path

from cuif_eval.pptx.render import render_pptx_previews


def test_png_rendering_or_structured_fallback_is_available(toy_task, tmp_path):
    result = render_pptx_previews(toy_task / "mock_outputs" / "final" / "result.pptx", tmp_path / "previews", "final")
    assert result["status"] in {"rendered", "fallback"}
    assert Path(result["summary"]).exists()
    assert Path(result["html"]).exists()
    if result["status"] == "rendered":
        assert result["images"], result
        assert all(Path(image).suffix == ".png" and Path(image).exists() for image in result["images"])
    else:
        assert result["images"] == []
        assert "message" in result
