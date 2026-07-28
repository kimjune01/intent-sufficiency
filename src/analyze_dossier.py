"""Analyze dossier v2 pairs with the nondeterminism control.

Control:   q1 vs q2 (identical condition run twice) — baseline disagreement.
Treatment: q1 vs h  (history added) — treated disagreement.
Dossier effect is the EXCESS of treated over control disagreement, not the
raw treated rate. Output validity is classified before bucketing; malformed
outputs (markdown, code fences, multi-paragraph prose, errors) are excluded
from intent counts rather than silently counted as intent.
"""

import json
import pathlib
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

THRESH = 0.85


def classify(s: str) -> str:
    t = s.strip()
    if t.startswith("ERROR"):
        return "error"
    if t.strip('"').upper() == "NONE":
        return "none"
    if not t or len(t) > 300 or "```" in t or t.startswith(("#", "|", "**")) or t.count("\n") > 1:
        return "invalid"
    return "intent"


def bucket(a: str, b: str, model) -> tuple[str, float | None]:
    ca, cb = classify(a), classify(b)
    if "error" in (ca, cb) or "invalid" in (ca, cb):
        return ("excluded", None)
    if ca == cb == "none":
        return ("both_none", None)
    if ca == "none":
        return ("none_to_intent", None)
    if cb == "none":
        return ("intent_to_none", None)
    e = model.encode([a, b])
    cos = float(e[0] @ e[1] / (np.linalg.norm(e[0]) * np.linalg.norm(e[1])))
    return ("same" if cos >= THRESH else "changed", round(cos, 3))


def table(pairs, model, label):
    counts, cosines, examples = {}, [], {}
    for r, (a, b) in pairs:
        k, cos = bucket(a, b, model)
        counts[k] = counts.get(k, 0) + 1
        if cos is not None:
            cosines.append(cos)
        if k in ("changed", "none_to_intent", "intent_to_none"):
            examples.setdefault(k, []).append((r, a, b, cos))
    n = sum(counts.values())
    valid = n - counts.get("excluded", 0)
    disagree = sum(counts.get(k, 0) for k in ("changed", "none_to_intent", "intent_to_none"))
    print(f"\n== {label}  (n={n}, valid={valid})")
    for k in ("both_none", "same", "changed", "none_to_intent", "intent_to_none", "excluded"):
        if counts.get(k):
            print(f"  {k:15} {counts[k]:3}  ({counts[k]/n:.1%})")
    print(f"  disagreement / valid: {disagree}/{valid} = {disagree/max(valid,1):.1%}")
    if cosines:
        print(f"  intent-pair cosines: n={len(cosines)} min={min(cosines)} "
              f"median={sorted(cosines)[len(cosines)//2]} max={max(cosines)}")
    return disagree, valid, examples


def main() -> None:
    root = pathlib.Path(__file__).parent.parent
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "results" / "dossier_haiku_v2.jsonl"
    lines = list(path.open())
    header = json.loads(lines[0])
    rows = [json.loads(l) for l in lines[1:]]
    print("run_config:", json.dumps(header["run_config"]))
    print(f"pairs: {len(rows)}")

    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    ctrl_d, ctrl_v, _ = table([(r, (r["intent_q1"], r["intent_q2"])) for r in rows], model, "CONTROL q1 vs q2")
    trt_d, trt_v, ex = table([(r, (r["intent_q1"], r["intent_h"])) for r in rows], model, "TREATMENT q1 vs h")

    print(f"\nexcess disagreement (treatment - control): "
          f"{trt_d/max(trt_v,1):.1%} - {ctrl_d/max(ctrl_v,1):.1%} = "
          f"{trt_d/max(trt_v,1) - ctrl_d/max(ctrl_v,1):+.1%}")

    for k, items in ex.items():
        print(f"\n— treatment {k}:")
        for r, a, b, cos in items:
            c = f" cos={cos}" if cos is not None else ""
            print(f"  [{r['target_hash'][:8]}{c} prior_incl={r['n_prior_included']}]")
            print(f"    Q1: {a[:110]}")
            print(f"    H:  {b[:110]}")


if __name__ == "__main__":
    main()
