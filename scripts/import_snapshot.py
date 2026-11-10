#!/usr/bin/env python3
"""Import the fixed Wayback snapshot into archive/source.html and data/releases.json."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_URL = (
    "https://web.archive.org/web/20220207223122id_/"
    "https://wiki.codeaurora.org/xwiki/bin/QAEP/release"
)
EXPECTED_HEADERS = [
    "date", "tag / build id", "chipset", "manifest", "android version"
]


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def parse_date(value: str) -> str:
    value = clean(value)
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def extract_records(html: bytes) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        header_cells = rows[0].find_all(["th", "td"], recursive=False)
        headers = [clean(cell.get_text(" ", strip=True)).lower() for cell in header_cells]
        normalized = [re.sub(r"\s+", " ", h) for h in headers]
        if normalized[:5] != EXPECTED_HEADERS:
            continue

        records = []
        for row_number, tr in enumerate(rows[1:], start=1):
            cells = tr.find_all(["td", "th"], recursive=False)
            if len(cells) < 5:
                continue
            values = [clean(c.get_text(" ", strip=True)) for c in cells[:5]]
            if not any(values):
                continue
            date, tag, chipset, manifest, android_version = values
            records.append({
                "date": date,
                "date_iso": parse_date(date),
                "tag": tag,
                "chipset": chipset,
                "manifest": manifest,
                "android_version": android_version,
                "source_row": row_number,
            })
        if records:
            return records

    # Some XWiki exports can place the header in a thead or use nested wrappers.
    # Fall back to all rows and locate the header by its text.
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for header_index, tr in enumerate(rows):
            cells = tr.find_all(["th", "td"])
            headers = [clean(c.get_text(" ", strip=True)).lower() for c in cells]
            if headers[:5] != EXPECTED_HEADERS:
                continue
            records = []
            for row_number, data_row in enumerate(rows[header_index + 1:], start=1):
                data_cells = data_row.find_all(["td", "th"])
                if len(data_cells) < 5:
                    continue
                vals = [clean(c.get_text(" ", strip=True)) for c in data_cells[:5]]
                if not any(vals):
                    continue
                date, tag, chipset, manifest, android_version = vals
                records.append({
                    "date": date,
                    "date_iso": parse_date(date),
                    "tag": tag,
                    "chipset": chipset,
                    "manifest": manifest,
                    "android_version": android_version,
                    "source_row": row_number,
                })
            if records:
                return records
    raise RuntimeError("Could not locate the expected five-column release table.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Use an already-downloaded HTML file")
    parser.add_argument("--url", default=SNAPSHOT_URL, help="Snapshot URL (default: pinned 2022-02-07 capture)")
    args = parser.parse_args()

    archive_dir = ROOT / "archive"
    data_dir = ROOT / "data"
    archive_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)
    html_path = archive_dir / "source.html"

    if args.input:
        source_path = args.input.resolve()
        if not source_path.is_file():
            print(f"Input file not found: {source_path}", file=sys.stderr)
            return 2
        html = source_path.read_bytes()
        if source_path != html_path:
            html_path.write_bytes(html)
    else:
        print(f"Downloading pinned snapshot:\n{args.url}")
        response = requests.get(
            args.url,
            timeout=90,
            headers={"User-Agent": "CAF-Release-Archive/0.1 (historical data preservation)"},
        )
        response.raise_for_status()
        html = response.content
        if len(html) < 10_000:
            raise RuntimeError(f"Downloaded HTML looks unexpectedly small ({len(html)} bytes).")
        html_path.write_bytes(html)

    records = extract_records(html)
    if len(records) < 100:
        raise RuntimeError(
            f"Only {len(records)} rows extracted; refusing to treat this as a complete import."
        )

    output = {
        "schema_version": 1,
        "source": "CodeAurora XWiki - Android releases",
        "snapshot_url": "https://web.archive.org/web/20220207223122/https://wiki.codeaurora.org/xwiki/bin/QAEP/release",
        "snapshot_timestamp": "20220207223122",
        "imported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "record_count": len(records),
        "records": records,
    }
    out_path = data_dir / "releases.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(records):,} rows.")
    print(f"Original HTML: {html_path.relative_to(ROOT)} ({len(html):,} bytes)")
    print(f"Normalized data: {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
