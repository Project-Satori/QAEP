#!/usr/bin/env python3
"""Build year-sharded static JSON and copy the frontend into site/."""
from __future__ import annotations
import json
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "releases.json"
SITE = ROOT / "site"


def main():
    if not SOURCE.is_file():
        raise SystemExit("Missing data/releases.json. Run scripts/import_snapshot.py first.")
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not records:
        raise SystemExit("Dataset is empty; refusing to build an empty archive.")

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "data").mkdir(parents=True)

    by_year = defaultdict(list)
    for record in records:
        year = (record.get("date_iso") or "")[:4] or "undated"
        by_year[year].append(record)

    index = {
        "schema_version": 1,
        "source": payload.get("source"),
        "snapshot_url": payload.get("snapshot_url"),
        "snapshot_timestamp": payload.get("snapshot_timestamp"),
        "record_count": len(records),
        "years": [],
    }
    for year in sorted(by_year.keys(), reverse=True):
        filename = f"{year}.json"
        shard = by_year[year]
        (SITE / "data" / filename).write_text(
            json.dumps(shard, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        index["years"].append({"year": year, "count": len(shard), "file": filename})

    (SITE / "data" / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name in ("index.html", "app.js", "style.css"):
        shutil.copy2(ROOT / "web" / name, SITE / name)
    print(f"Built {len(records):,} records across {len(by_year)} year shards.")


if __name__ == "__main__":
    main()
