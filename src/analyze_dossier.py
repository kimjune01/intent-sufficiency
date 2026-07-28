"""Analyze the dossier-redundancy pairs.

Buckets per pre-registration (worklog 2026-07-28):
  both-NONE        — no intent either way; dossier changed nothing
  same-intent      — both non-NONE, cosine >= 0.85 (BGE-small): dossier redundant
  changed-intent   — both non-NONE, cosine < 0.85: dossier changed the match
  none->intent     — history SURFACED intent absent from the conversation
  intent->none     — history suppressed intent
  error            — either side errored

Prints the bucket table and every changed/flipped pair for eyeballing.
"""

import json
import pathlib
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

THRESH = 0.85


def is_none(s: str) -> bool:
    return s.strip().strip('"').upper() == "NONE"


def main() -> None:
    path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                        pathlib.Path(__file__).parent.parent / "results" / "dossier_haiku.jsonl")
    rows = [json.loads(l) for l in path.open()]

    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    buckets = {k: [] for k in ("both_none", "same_intent", "changed_intent",
                               "none_to_intent", "intent_to_none", "error")}
    for r in rows:
        q, h = r["intent_q"], r["intent_h"]
        if q.startswith("ERROR") or h.startswith("ERROR"):
            buckets["error"].append(r)
        elif is_none(q) and is_none(h):
            buckets["both_none"].append(r)
        elif is_none(q) and not is_none(h):
            buckets["none_to_intent"].append(r)
        elif not is_none(q) and is_none(h):
            buckets["intent_to_none"].append(r)
        else:
            e = model.encode([q, h])
            cos = float(e[0] @ e[1] / (np.linalg.norm(e[0]) * np.linalg.norm(e[1])))
            r["cos"] = round(cos, 3)
            buckets["same_intent" if cos >= THRESH else "changed_intent"].append(r)

    n = len(rows)
    print(f"pairs: {n}")
    for k, v in buckets.items():
        print(f"  {k:15} {len(v):3}  ({len(v)/n:.1%})")

    valid = n - len(buckets["error"])
    material = len(buckets["changed_intent"]) + len(buckets["none_to_intent"]) + len(buckets["intent_to_none"])
    print(f"\nmaterial-change rate (changed + flips) / valid: {material}/{valid} = {material/valid:.1%}")
    print(f"pre-registered: material <20%, none->intent <10%")

    for k in ("changed_intent", "none_to_intent", "intent_to_none"):
        if buckets[k]:
            print(f"\n— {k}:")
            for r in buckets[k]:
                cos = f" cos={r['cos']}" if "cos" in r else ""
                print(f"  [{r['target_hash'][:8]}{cos} hist={r['n_history_convs']}]")
                print(f"    Q: {r['intent_q'][:110]}")
                print(f"    H: {r['intent_h'][:110]}")


if __name__ == "__main__":
    main()
