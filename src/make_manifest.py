"""Emit content-free pointers to the exact data used.

data/MANIFEST.json — fetch parameters + conversation_hash list: enough to
reconstruct the identical sample from the public API (WildChat rows carry a
stable conversation_hash), without redistributing any conversation text.

results/labels_<run>.json — per-run outcome labels keyed by hash
(intent / none / error), so every reported rate is checkable row-by-row
against a reconstruction.
"""

import json
import pathlib

root = pathlib.Path(__file__).parent.parent
sample = root / "data" / "sample_2000.jsonl"

rows = [json.loads(l) for l in sample.open()]
manifest = {
    "dataset": "allenai/WildChat-1M",
    "access": "https://datasets-server.huggingface.co/rows (public, no auth)",
    "fetch": {
        "script": "src/fetch_sample.py",
        "total_rows_public_view": 837_989,
        "pages": 20,
        "page_size": 100,
        "offset_rule": "page * (total_rows // pages)",
        "fields_kept": ["conversation_hash", "model", "timestamp", "country", "language", "user turns only"],
    },
    "conversations": len(rows),
    "conversation_hashes": [r["hash"] for r in rows],
}
(root / "data" / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")

def label(intent: str) -> str:
    s = intent.strip().strip('"').upper()
    if intent.startswith("ERROR"):
        return "error"
    return "none" if s == "NONE" else "intent"

for f in (root / "results").glob("intent_*.jsonl"):
    if "INVALID" in f.name:
        continue
    labels = {r["hash"]: label(r["intent"]) for r in map(json.loads, f.open())}
    out = root / "results" / f"labels_{f.stem}.json"
    out.write_text(json.dumps(labels, indent=0, sort_keys=True) + "\n")
    print(f"{out.name}: {len(labels)} rows")

print(f"MANIFEST.json: {len(rows)} hashes")
