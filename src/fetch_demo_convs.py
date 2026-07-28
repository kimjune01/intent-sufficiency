"""Refetch full conversations (both roles) for demo-selected hashes.

Selection: every non-NONE extraction from the wrapped run, plus a sample of
NONEs (the proximity dot staying dark on casual chats is part of the demo).
Skips rows WildChat flags toxic. Writes data/demo_convs.json.
"""

import json
import pathlib
import random
import time

import requests

TOTAL_ROWS = 837_989
PAGES, PAGE = 20, 100
STRIDE = TOTAL_ROWS // PAGES
MAX_MSGS = 8
N_NONE = 15

root = pathlib.Path(__file__).parent.parent

results = [json.loads(l) for l in (root / "results" / "intent_claude_haiku_wrapped.jsonl").open()]
def is_none(s): return s.strip().strip('"').upper() == "NONE"
intents = {r["hash"]: r["intent"] for r in results
           if not is_none(r["intent"]) and not r["intent"].startswith("ERROR")}
nones = [r["hash"] for r in results if is_none(r["intent"])]
wanted = set(intents) | set(random.Random(0).sample(nones, min(N_NONE, len(nones))))
print(f"want {len(wanted)} conversations ({len(intents)} intent, rest NONE)")

out = []
for p in range(PAGES):
    base = p * STRIDE
    for attempt in range(8):
        r = requests.get(
            "https://datasets-server.huggingface.co/rows",
            params={"dataset": "allenai/WildChat-1M", "config": "default",
                    "split": "train", "offset": base, "length": PAGE},
            timeout=60,
        )
        if r.status_code == 200:
            break
        time.sleep(30 if r.status_code == 429 else 10 * (attempt + 1))
    r.raise_for_status()
    time.sleep(3)
    for row in r.json()["rows"]:
        c = row["row"]
        h = c["conversation_hash"]
        if h not in wanted or c.get("toxic"):
            continue
        msgs = [{"role": t["role"], "content": t["content"]}
                for t in c["conversation"] if t.get("content")][:MAX_MSGS]
        out.append({
            "hash": h,
            "language": (c["conversation"][0].get("language") if c["conversation"] else None),
            "intent": intents.get(h),  # None => NONE case
            "messages": msgs,
        })
    print(f"page {p + 1}/{PAGES}: {len(out)} collected", flush=True)

(root / "data" / "demo_convs.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print(f"wrote {len(out)} full conversations")
