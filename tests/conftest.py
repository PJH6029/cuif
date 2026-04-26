from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TOY_TASK = ROOT / "poc" / "tasks" / "toy_pptx_layout"


@pytest.fixture
def toy_task() -> Path:
    return TOY_TASK


@pytest.fixture
def copied_task(tmp_path: Path) -> Path:
    dst = tmp_path / "toy_pptx_layout"
    shutil.copytree(TOY_TASK, dst)
    return dst


def load_manifest_dict(task: Path) -> dict:
    return yaml.safe_load((task / "manifest.yaml").read_text(encoding="utf-8"))


def write_manifest_dict(task: Path, data: dict) -> Path:
    path = task / "manifest.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def mutate_manifest(copied_task: Path):
    def _mutate(fn):
        data = load_manifest_dict(copied_task)
        data = copy.deepcopy(data)
        fn(data)
        write_manifest_dict(copied_task, data)
        return copied_task / "manifest.yaml"

    return _mutate
