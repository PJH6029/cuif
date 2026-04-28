from __future__ import annotations

import pytest

from cuif_eval.schema import ManifestValidationError, load_manifest


def test_valid_toy_manifest_loads(toy_task):
    manifest = load_manifest(toy_task / "manifest.yaml")
    assert manifest.id == "toy_pptx_layout"
    assert len(manifest.turns) == 2
    assert manifest.primary_artifact_family == "pptx"
    assert manifest.package_artifacts["seed"]["type"] == "pptx"
    assert manifest.turns[0].new_inputs.visual == ["package.sketch"]
    assert manifest.turns[1].new_inputs.refs() == []


def test_missing_package_artifact_fails(mutate_manifest):
    path = mutate_manifest(lambda data: data["artifacts"]["package"]["seed"].update({"path": "artifacts/missing.pptx"}))
    with pytest.raises(ManifestValidationError, match="missing"):
        load_manifest(path)


def test_missing_expected_output_declaration_fails(mutate_manifest):
    def mutate(data):
        del data["artifacts"]["expected_outputs"]["turn1"]["result"]
    path = mutate_manifest(mutate)
    with pytest.raises(ManifestValidationError, match="expected_output"):
        load_manifest(path)


def test_unknown_evaluator_duplicate_ids_bad_points_and_unknown_dep_fail(mutate_manifest):
    def mutate(data):
        check = data["turns"][0]["checks"][0]
        check["evaluator"] = "unknown_eval"
        check["points"] = -1
        data["turns"][0]["checks"][1]["id"] = check["id"]
        data["turns"][0]["checks"][2]["depends_on"] = ["missing_check"]
    path = mutate_manifest(mutate)
    with pytest.raises(ManifestValidationError) as exc:
        load_manifest(path)
    text = str(exc.value)
    assert "unknown evaluator" in text
    assert "duplicate check id" in text
    assert "points must be" in text
    assert "unknown check id" in text


def test_duplicate_turn_id_fails(mutate_manifest):
    path = mutate_manifest(lambda data: data["turns"][1].update({"id": "turn1"}))
    with pytest.raises(ManifestValidationError, match="duplicate turn id"):
        load_manifest(path)


def test_agent_facing_inputs_must_be_declared_by_turn(mutate_manifest):
    path = mutate_manifest(lambda data: data["turns"][0].pop("new_inputs"))
    with pytest.raises(ManifestValidationError, match="must be listed once"):
        load_manifest(path)


def test_turn_new_inputs_reject_duplicates_and_wrong_modality(mutate_manifest):
    def mutate(data):
        data["turns"][0]["new_inputs"] = {"textual": ["package.sketch"], "visual": ["package.sketch"]}
        data["turns"][1]["new_inputs"] = {"textual": [], "visual": ["package.sketch"]}
    path = mutate_manifest(mutate)
    with pytest.raises(ManifestValidationError) as exc:
        load_manifest(path)
    text = str(exc.value)
    assert "not supported for textual inputs" in text
    assert "repeats package.sketch" in text


def test_check_referencing_unknown_artifact_namespace_fails(mutate_manifest):
    path = mutate_manifest(lambda data: data["turns"][0]["checks"][0].update({"artifact": "run.previews.turn1.png"}))
    with pytest.raises(ManifestValidationError, match="unknown artifact namespace"):
        load_manifest(path)


def test_judge_missing_prompt_rubric_or_live_config_fails_when_required(mutate_manifest):
    def mutate(data):
        data["turns"][1]["checks"][-1]["optional"] = False
        data["turns"][1]["checks"][-1]["diagnostic"] = False
        data["turns"][1]["checks"][-1]["points"] = 1
        data["turns"][1]["checks"][-1]["params"] = {"prompt": "judge this"}
    path = mutate_manifest(mutate)
    with pytest.raises(ManifestValidationError) as exc:
        load_manifest(path, skip_judges=False)
    assert "prompt and rubric" in str(exc.value)
    assert "model/base_url" in str(exc.value)


def test_docx_metadata_validates_but_pptx_evaluator_on_docx_fails(mutate_manifest):
    def mutate(data):
        data["artifacts"]["expected_outputs"]["final"]["result"]["type"] = "docx"
    path = mutate_manifest(mutate)
    with pytest.raises(ManifestValidationError, match="PPTX evaluator"):
        load_manifest(path)
