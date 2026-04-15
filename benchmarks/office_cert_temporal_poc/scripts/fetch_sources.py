from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup
from requests.utils import requote_uri

from common import (
    METADATA_CACHE,
    RAW_CACHE,
    ROOT,
    download_response_to_file,
    ensure_dirs,
    load_yaml,
    now_utc,
    safe_filename,
    session,
    write_json,
)


def source_filter(source: dict, suite: str) -> bool:
    return suite == "all" or source.get("suite") == suite


def parse_cd_filename(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r"filename\*=UTF-8''([^;]+)", value, re.I)
    if m:
        return safe_filename(unquote(m.group(1)))
    m = re.search(r'filename="?([^";]+)"?', value, re.I)
    if m:
        return safe_filename(repair_legacy_korean_filename(unquote(m.group(1))))
    return None


def repair_legacy_korean_filename(value: str) -> str:
    # Some Korean public-sector download headers expose CP949 bytes decoded as
    # ISO-8859-1. Reconstruct the original bytes before falling back.
    if not any(ord(ch) > 127 for ch in value):
        return value
    try:
        return value.encode("latin-1").decode("cp949")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def fetch_static_files(source: dict, dry_run: bool) -> list[dict]:
    out = []
    s = session()
    for file_def in source.get("files", []):
        dest = RAW_CACHE / source["id"] / file_def["role"] / safe_filename(file_def["filename"])
        item = {
            "source_id": source["id"],
            "suite": source["suite"],
            "download_id": f'{source["id"]}::{file_def["role"]}::{file_def["filename"]}',
            "role": file_def["role"],
            "filename": file_def["filename"],
            "url": file_def["url"],
            "landing_page": source.get("landing_page"),
            "license_note": source.get("license_note"),
            "status": "dry_run" if dry_run else "pending",
        }
        if dry_run:
            out.append(item)
            continue
        response = s.get(requote_uri(file_def["url"]), stream=True, timeout=120)
        item["http_status"] = response.status_code
        if response.ok:
            item.update(download_response_to_file(response, dest))
            item["status"] = "downloaded"
        else:
            item["status"] = "failed"
            item["error"] = response.text[:500]
        out.append(item)
    return out


def list_kpc_board(source: dict, pages: int) -> list[dict]:
    s = session()
    board = source["board"]
    rows = []
    for page in range(1, pages + 1):
        response = s.post(
            board["list_url"],
            data={
                "bbsAttrbCode": board["bbs_attrb_code"],
                "bbsId": board["bbs_id"],
                "pageIndex": str(page),
            },
            timeout=60,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            match = re.search(r"boardDetail\((\d+)\)", link["href"])
            if not match:
                continue
            row_text = link.find_parent("td").get_text(" ", strip=True) if link.find_parent("td") else ""
            date_match = re.search(r"작성일\s*:\s*([0-9-]+)", row_text)
            rows.append(
                {
                    "ntt_id": match.group(1),
                    "title": link.get_text(" ", strip=True),
                    "posted_at": date_match.group(1) if date_match else None,
                    "page": page,
                }
            )
    return rows


def fetch_kpc_detail(source: dict, ntt_id: str) -> dict:
    s = session()
    board = source["board"]
    response = s.post(
        board["detail_url"],
        data={
            "bbsAttrbCode": board["bbs_attrb_code"],
            "bbsId": board["bbs_id"],
            "nttId": ntt_id,
            "pageIndex": "1",
        },
        timeout=60,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find(class_="h3")
    attachments = []
    for link in soup.find_all("a", href=True):
        match = re.search(r"fnDownload\('([^']+)'\s*,\s*'([^']+)'\)", link["href"])
        if not match:
            continue
        attachments.append(
            {
                "file_id": match.group(1),
                "file_seq": match.group(2),
                "filename": safe_filename(link.get_text(" ", strip=True)),
            }
        )
    return {
        "title": title.get_text(" ", strip=True) if title else None,
        "attachments": attachments,
    }


def fetch_kpc_latest(source: dict, dry_run: bool, pages: int) -> list[dict]:
    board = source["board"]
    rows = list_kpc_board(source, pages)
    selected = {}
    for key, rule in source["latest_items"].items():
        needle = rule["title_contains"]
        for row in rows:
            if needle in row["title"]:
                selected[key] = row
                break

    out = []
    s = session()
    for item_key, row in selected.items():
        detail = fetch_kpc_detail(source, row["ntt_id"])
        if not detail["attachments"]:
            out.append(
                {
                    "source_id": source["id"],
                    "suite": source["suite"],
                    "item_key": item_key,
                    "ntt_id": row["ntt_id"],
                    "title": row["title"],
                    "posted_at": row.get("posted_at"),
                    "status": "failed",
                    "error": "No attachments discovered",
                }
            )
            continue
        for attach in detail["attachments"]:
            filename = safe_filename(attach["filename"])
            dest = RAW_CACHE / source["id"] / item_key / filename
            record = {
                "source_id": source["id"],
                "suite": source["suite"],
                "download_id": f'{source["id"]}::{item_key}::{filename}',
                "item_key": item_key,
                "role": "archive",
                "filename": filename,
                "title": row["title"],
                "detail_title": detail.get("title"),
                "posted_at": row.get("posted_at"),
                "ntt_id": row["ntt_id"],
                "file_id": attach["file_id"],
                "file_seq": attach["file_seq"],
                "landing_page": source.get("landing_page"),
                "license_note": source.get("license_note"),
                "status": "dry_run" if dry_run else "pending",
            }
            if dry_run:
                out.append(record)
                continue
            response = s.post(
                board["download_url"],
                data={"fileId": attach["file_id"], "fileSeq": attach["file_seq"]},
                stream=True,
                timeout=180,
            )
            record["http_status"] = response.status_code
            if response.ok and "text/html" not in response.headers.get("content-type", "").lower():
                cd_name = parse_cd_filename(response.headers.get("content-disposition"))
                if cd_name and cd_name != filename:
                    dest = dest.with_name(cd_name)
                    record["filename"] = cd_name
                record.update(download_response_to_file(response, dest))
                record["status"] = "downloaded"
            else:
                record["status"] = "failed"
                record["error"] = response.text[:500]
            out.append(record)
    return out


def fetch_microsoft_learn(source: dict, dry_run: bool, include_large: bool) -> list[dict]:
    s = session()
    response = s.get(source["landing_page"], timeout=90)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    heading_to_key = {p["heading"]: p["key"] for p in source.get("products", [])}
    out = []
    for h2 in soup.find_all("h2"):
        heading = h2.get_text(" ", strip=True)
        if heading not in heading_to_key:
            continue
        product_key = heading_to_key[heading]
        section_links = []
        for node in h2.find_all_next():
            if node.name == "h2":
                break
            if node.name == "a" and node.get("href") and "download.microsoft.com" in node["href"]:
                section_links.append(node)
        for i, link in enumerate(section_links, start=1):
            href = link["href"]
            filename = safe_filename(link.get_text(" ", strip=True) or f"{product_key}_{i}")
            record = {
                "source_id": source["id"],
                "suite": source["suite"],
                "download_id": f'{source["id"]}::{product_key}::{i}',
                "item_key": product_key,
                "role": "course_materials",
                "filename": filename,
                "url": href,
                "title": heading,
                "landing_page": source.get("landing_page"),
                "license_note": source.get("license_note"),
                "status": "metadata_only",
            }
            if include_large and not dry_run:
                dest = RAW_CACHE / source["id"] / product_key / filename
                dl_response = s.get(href, stream=True, timeout=240)
                record["http_status"] = dl_response.status_code
                if dl_response.ok:
                    cd_name = parse_cd_filename(dl_response.headers.get("content-disposition"))
                    if cd_name:
                        dest = dest.with_name(cd_name)
                        record["filename"] = cd_name
                    record.update(download_response_to_file(dl_response, dest))
                    record["status"] = "downloaded"
                else:
                    record["status"] = "failed"
                    record["error"] = dl_response.text[:500]
            elif dry_run:
                record["status"] = "dry_run_metadata_only"
            out.append(record)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="all", choices=["all", "computer_skills_1", "itq", "mos"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-large", action="store_true")
    parser.add_argument("--kpc-pages", type=int, default=2)
    args = parser.parse_args()

    ensure_dirs()
    manifest = load_yaml(ROOT / "sources.yml")
    result = {
        "generated_at": now_utc(),
        "dry_run": args.dry_run,
        "suite": args.suite,
        "downloads": [],
    }
    for source in manifest.get("sources", []):
        if not source_filter(source, args.suite):
            continue
        method = source.get("download_method")
        if method == "static_files":
            result["downloads"].extend(fetch_static_files(source, args.dry_run))
        elif method == "kpc_board_latest":
            result["downloads"].extend(fetch_kpc_latest(source, args.dry_run, args.kpc_pages))
        elif method == "microsoft_learn_links":
            result["downloads"].extend(fetch_microsoft_learn(source, args.dry_run, args.include_large))
        else:
            result["downloads"].append(
                {
                    "source_id": source.get("id"),
                    "status": "failed",
                    "error": f"Unsupported download_method: {method}",
                }
            )

    if args.dry_run:
        print(f"Dry-run discovered {len(result['downloads'])} downloadable or metadata items.")
        for item in result["downloads"]:
            label = item.get("filename") or item.get("title")
            print(f"- {item.get('source_id')} {item.get('item_key', '')} {item.get('role')}: {label} [{item.get('status')}]")
    else:
        write_json(METADATA_CACHE / "fetch_index.json", result)
        print(f"Wrote {METADATA_CACHE / 'fetch_index.json'} with {len(result['downloads'])} records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
