"""Generate demo/src/wildchat.ts from data/demo_convs.json.

Real WildChat conversations as picker entries for the vectorspace demo.
Labels derive from the wrapped-run extraction (or the opening user turn for
NONE cases, marked offTopic). Message content is capped for display sanity;
the demo re-runs live extraction on whatever is loaded, so the stored intent
is only used for the label.
"""

import json
import pathlib

MAX_CONTENT = 800
ROOT = pathlib.Path(__file__).parent.parent
DEMO_TS = pathlib.Path.home() / "Documents" / "vectorspace-adserver" / "demo" / "src" / "wildchat.ts"


def label_for(c: dict) -> str:
    if c["intent"]:
        s = c["intent"].strip().strip('"')
        for cut in (" for ", ", ", " targeting "):
            if cut in s:
                s = s.split(cut)[0]
                break
        return (s[:38] + "…") if len(s) > 39 else s
    first = c["messages"][0]["content"].strip().replace("\n", " ")
    return (first[:34] + "…") if len(first) > 35 else first


def ts_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


convs = json.loads((ROOT / "data" / "demo_convs.json").read_text())
convs.sort(key=lambda c: (c["intent"] is None, label_for(c).lower()))

lines = [
    "// Real conversations sampled from WildChat-1M (allenai/WildChat-1M, AI2 ImpACT",
    "// license) — a corpus of real user-ChatGPT conversations. Sampled and labeled by",
    "// https://github.com/kimjune01/intent-sufficiency; each entry's comment is the",
    "// conversation_hash for reproducibility. Labels come from the shipped intent-",
    "// extraction prompt; offTopic entries extracted NONE.",
    'import type { Conversation } from "./conversations";',
    "",
    "export const wildchatConversations: Conversation[] = [",
]
for c in convs:
    lines.append(f"  // {c['hash']}")
    lines.append(f"  {{")
    lines.append(f"    label: {ts_str(label_for(c))},")
    if not c["intent"]:
        lines.append("    offTopic: true,")
    lines.append("    messages: [")
    for m in c["messages"]:
        content = m["content"]
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + " […]"
        role = m["role"] if m["role"] in ("user", "assistant") else "user"
        lines.append(f"      {{ role: {ts_str(role)}, content: {ts_str(content)} }},")
    lines.append("    ],")
    lines.append("  },")
lines.append("];")
lines.append("")

DEMO_TS.write_text("\n".join(lines))
print(f"wrote {len(convs)} conversations to {DEMO_TS}")
