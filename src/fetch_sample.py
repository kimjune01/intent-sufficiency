"""Fetch a reproducible sample of WildChat-1M via the HF datasets-server rows API.

The rows API serves 100 rows per request without auth. We take PAGES pages at
deterministic offsets spread across the 1M rows (seeded stride, not row 0-2000,
to avoid the dataset's insertion-order bias toward early-2023 traffic).

Writes data/sample_<n>.jsonl with one conversation per line:
  {hash, model, timestamp, country, language, turns: [user texts only]}
User turns only: ad matching sees what the user volunteered. Assistant text
would leak the model's elaborations into the sufficiency measurement.
"""

import json
import pathlib
import sys
import time

import requests

API = "https://datasets-server.huggingface.co/rows"
DATASET = "allenai/WildChat-1M"
TOTAL_ROWS = 837_989  # rows served by the public datasets-server view (checked 2026-07-28)
PAGE = 100
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 20
STRIDE = TOTAL_ROWS // PAGES

out = pathlib.Path(__file__).parent.parent / "data" / f"sample_{PAGES * PAGE}.jsonl"
out.parent.mkdir(exist_ok=True)

n = 0
with out.open("w") as f:
    for p in range(PAGES):
        offset = p * STRIDE
        for attempt in range(8):
            r = requests.get(
                API,
                params={
                    "dataset": DATASET,
                    "config": "default",
                    "split": "train",
                    "offset": offset,
                    "length": PAGE,
                },
                timeout=60,
            )
            if r.status_code == 200:
                break
            wait = 30 if r.status_code == 429 else 10 * (attempt + 1)
            print(f"  {r.status_code} at offset {offset}, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
        r.raise_for_status()
        time.sleep(3)  # stay under the rows-API rate limit
        for row in r.json()["rows"]:
            c = row["row"]
            turns = [
                t["content"]
                for t in c["conversation"]
                if t.get("role") == "user" and t.get("content")
            ]
            if not turns:
                continue
            first = c["conversation"][0]
            f.write(
                json.dumps(
                    {
                        "hash": c["conversation_hash"],
                        "model": c["model"],
                        "timestamp": c["timestamp"],
                        "country": first.get("country"),
                        "language": first.get("language"),
                        "turns": turns,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            n += 1
        print(f"page {p + 1}/{PAGES} (offset {offset}): {n} conversations", file=sys.stderr)

print(f"wrote {n} conversations to {out}")
