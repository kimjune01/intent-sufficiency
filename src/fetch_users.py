"""Fetch contiguous WildChat blocks keeping hashed_ip, for the dossier-redundancy
experiment. Contiguous (not strided) because a user's conversations cluster in
time, so contiguous blocks maximize users with >=2 conversations in-sample.

Writes data/sample_users.jsonl. hashed_ip stays local (data/ is gitignored).
"""

import json
import pathlib
import sys
import time

import requests

API = "https://datasets-server.huggingface.co/rows"
DATASET = "allenai/WildChat-1M"
PAGE = 100
# four contiguous 1000-row blocks spread across the public view
BLOCKS = [50_000, 250_000, 450_000, 650_000]
PAGES_PER_BLOCK = 10

out = pathlib.Path(__file__).parent.parent / "data" / "sample_users.jsonl"
n = 0
with out.open("w") as f:
    for base in BLOCKS:
        for p in range(PAGES_PER_BLOCK):
            offset = base + p * PAGE
            for attempt in range(8):
                r = requests.get(
                    API,
                    params={"dataset": DATASET, "config": "default",
                            "split": "train", "offset": offset, "length": PAGE},
                    timeout=60,
                )
                if r.status_code == 200:
                    break
                time.sleep(30 if r.status_code == 429 else 10 * (attempt + 1))
            r.raise_for_status()
            time.sleep(3)
            for row in r.json()["rows"]:
                c = row["row"]
                turns = [t["content"] for t in c["conversation"]
                         if t.get("role") == "user" and t.get("content")]
                if not turns:
                    continue
                f.write(json.dumps({
                    "hash": c["conversation_hash"],
                    "hashed_ip": c.get("hashed_ip"),
                    "timestamp": c["timestamp"],
                    "language": c.get("language"),
                    "turns": turns,
                }, ensure_ascii=False) + "\n")
                n += 1
        print(f"block {base}: cumulative {n}", file=sys.stderr)

print(f"wrote {n} conversations to {out}")
