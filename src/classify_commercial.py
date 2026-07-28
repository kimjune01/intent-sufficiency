"""Deterministic commercial-intent screen over a fetched sample.

A conversation is flagged when any user turn matches a category's pattern.
This is a high-recall screen for a learning-scale sample; precision gets
established by the manual review file it emits (review_hits / review_misses),
not assumed. Nothing here is a sufficiency judgment — that comes after the
screen survives review.

Usage: classify_commercial.py data/sample_2000.jsonl
Writes results/commercial_rate.json and results/review_{hits,misses}.jsonl
"""

import json
import pathlib
import random
import re
import sys

CATEGORIES = {
    "shopping": r"\b(buy|purchase|recommend(?:ation)?s?|best|cheapest|price|worth it|review|compare|alternative(?:s)? to|which (?:one|brand|model))\b.{0,80}\b(laptop|phone|headphone|camera|monitor|keyboard|mattress|shoe|watch|bike|car|tv|appliance|vacuum|blender|gift|product|brand|model)\b",
    "travel": r"\b(flight|hotel|airbnb|itinerary|book(?:ing)?|visit|trip to|travel to|vacation|resort|hostel|things to do in)\b",
    "food_local": r"\b(restaurant|cafe|bar|near me|delivery|takeout|reservation)\b",
    "software": r"\b(best|recommend|which|alternative(?:s)? to|vs\.?|compare)\b.{0,60}\b(app|software|tool|platform|service|subscription|vpn|hosting|crm|saas)\b",
    "services": r"\b(hire|find|need)\b.{0,40}\b(lawyer|attorney|accountant|plumber|electrician|contractor|therapist|tutor|photographer|agent)\b|\b(insurance|mortgage|loan|credit card)\b.{0,40}\b(best|recommend|which|should i|compare)\b",
    "how_to_buy": r"\b(where (?:can|do|should) i (?:buy|get|find|order)|how much (?:does|do|is|are)|is it worth (?:buying|getting))\b",
}

PATTERNS = {k: re.compile(v, re.IGNORECASE) for k, v in CATEGORIES.items()}

path = pathlib.Path(sys.argv[1])
results_dir = path.parent.parent / "results"
results_dir.mkdir(exist_ok=True)

convs = [json.loads(l) for l in path.open()]
rng = random.Random(0)

hits, misses = [], []
counts = {k: 0 for k in CATEGORIES}
for c in convs:
    text = "\n".join(c["turns"])
    matched = {k for k, p in PATTERNS.items() if p.search(text)}
    if matched:
        for k in matched:
            counts[k] += 1
        hits.append({**c, "categories": sorted(matched)})
    else:
        misses.append(c)

english = sum(1 for c in convs if (c.get("language") or "").lower() == "english")
report = {
    "sample_file": path.name,
    "conversations": len(convs),
    "english": english,
    "commercial_any": len(hits),
    "commercial_rate": round(len(hits) / len(convs), 4),
    "by_category": counts,
}
(results_dir / "commercial_rate.json").write_text(json.dumps(report, indent=2) + "\n")

for name, pool, n in (("review_hits", hits, 40), ("review_misses", misses, 40)):
    sample = rng.sample(pool, min(n, len(pool)))
    with (results_dir / f"{name}.jsonl").open("w") as f:
        for c in sample:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(json.dumps(report, indent=2))
