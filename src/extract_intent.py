"""Run the shipped Vector Space intent-extraction prompt over sampled conversations.

Prompt is verbatim from vectorspace-adserver/sdk-web/src/intent.ts (the deployed
mechanism), run against a local model via ollama. Output is append-only jsonl
keyed by conversation hash, so reruns resume.

The denominator measurement: share of conversations where the prompt returns a
position sentence instead of NONE, with no profile data available by construction.

Usage: extract_intent.py data/sample_2000.jsonl [n_conversations] [model]
"""

import json
import pathlib
import random
import sys

import requests

# verbatim from sdk-web/src/intent.ts (INTENT_PROMPT)
INTENT_PROMPT = """Given a conversation, decide whether the person could benefit from a professional service. If yes, write a single sentence describing that service — as if the provider were writing their own position statement. If the conversation is casual, off-topic, or doesn't suggest any professional need, respond with exactly "NONE".

Format: [value prop] + [ideal client profile] + [qualifier]
Example: "Sports injury knee rehab for competitive endurance athletes recovering from overuse."

Rules:
- Match the most obvious need. A health complaint needs a health provider, not a lawyer. A legal issue needs legal help, not a therapist.
- Be specific to the situation but don't embellish beyond what's stated.
- Do NOT extract demographics or personal data about the user.
- If there is no clear professional need, respond with "NONE".

Respond with ONLY the one-sentence service description or "NONE", nothing else."""

MAX_CHARS = 4000  # first user turns, truncated: what the SDK would see early


def load_sampled(path: pathlib.Path, n: int) -> list[dict]:
    """Seeded shuffle shared by every backend so per-conversation results align."""
    convs = [json.loads(l) for l in path.open()]
    random.Random(0).shuffle(convs)
    return convs[:n]


def summarize(out: pathlib.Path, label: str) -> None:
    rows = [json.loads(l) for l in out.open()]
    none = sum(1 for r in rows if r["intent"].strip().strip('"').upper() == "NONE")
    print(
        json.dumps(
            {"model": label, "extracted": len(rows), "none": none,
             "non_none_rate": round(1 - none / len(rows), 4)},
            indent=2,
        )
    )


def main() -> None:
    path = pathlib.Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    model = sys.argv[3] if len(sys.argv) > 3 else "llama3.2:3b"

    out = path.parent.parent / "results" / f"intent_{model.replace(':', '_')}.jsonl"
    done = {json.loads(l)["hash"] for l in out.open()} if out.exists() else set()

    todo = [c for c in load_sampled(path, n) if c["hash"] not in done]
    print(f"{len(todo)} to extract ({len(done)} already done)", file=sys.stderr)

    with out.open("a") as f:
        for i, c in enumerate(todo):
            text = "\n".join(c["turns"][:3])[:MAX_CHARS]
            r = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": INTENT_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 80},
                },
                timeout=120,
            )
            r.raise_for_status()
            intent = r.json()["message"]["content"].strip()
            f.write(
                json.dumps(
                    {"hash": c["hash"], "language": c.get("language"), "intent": intent},
                    ensure_ascii=False,
                )
                + "\n"
            )
            f.flush()
            if (i + 1) % 25 == 0:
                print(f"{i + 1}/{len(todo)}", file=sys.stderr)

    summarize(out, model)


if __name__ == "__main__":
    main()
