from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CACHE = ROOT / "cache"
RAW_CACHE = CACHE / "raw"
UNPACKED_CACHE = CACHE / "unpacked"
METADATA_CACHE = CACHE / "metadata"
RUNS = ROOT / "runs"
WORKSPACES = RUNS / "workspaces"
GOLD = RUNS / "gold"
RENDERS = RUNS / "rendered"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    for path in (RAW_CACHE, UNPACKED_CACHE, METADATA_CACHE, WORKSPACES, GOLD, RENDERS):
        path.mkdir(parents=True, exist_ok=True)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    return s


def safe_filename(name: str) -> str:
    name = name.strip().replace("\\", "_").replace("/", "_")
    name = re.sub(r"\s+", " ", name)
    return name or "download"


def safe_id(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9_.-]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_response_to_file(response: requests.Response, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    size = 0
    with tmp.open("wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                size += len(chunk)
                f.write(chunk)
    tmp.replace(dest)
    return {
        "path": str(dest.relative_to(ROOT)),
        "bytes": size,
        "sha256": sha256_file(dest),
        "content_type": response.headers.get("content-type"),
        "content_disposition": response.headers.get("content-disposition"),
    }


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_file_unique(src: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    candidate = dest_dir / src.name
    if not candidate.exists():
        shutil.copy2(src, candidate)
        return candidate
    stem = src.stem
    suffix = src.suffix
    for i in range(2, 1000):
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            shutil.copy2(src, candidate)
            return candidate
    raise RuntimeError(f"Could not create unique destination for {src}")


GOLD_KEYWORDS = ("정답", "모범", "해설", "solution", "answer", "answers", "solved")
ANSWER_BUT_NOT_GOLD = ("답안작성", "답안 작성", "작성요령", "작성 요령")


def role_from_name(name: str) -> str:
    low = name.lower()
    compact = re.sub(r"\s+", "", name)
    if any(k in low or k in name for k in GOLD_KEYWORDS):
        if not any(k in compact or k in name for k in ANSWER_BUT_NOT_GOLD):
            return "gold"
    if low.endswith((".pdf", ".txt", ".md")):
        return "problem"
    return "input"


def is_archive(path: Path) -> bool:
    return path.suffix.lower() in {".zip"}
