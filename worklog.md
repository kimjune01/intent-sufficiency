# worklog

## 2026-07-28 — project start
- Claim under test + decomposition in README. Learning-scale first.
- WildChat-1M reachable unauthenticated via HF datasets-server rows API;
  public view serves 837,989 rows (not 1M — gated remainder). Offsets past
  that return empty. Rate limit is real: ~429 after bursts, 3s/request is safe.
- fetch_sample.py: 20 deterministic offsets × 100 rows, user turns only.
- classify_commercial.py: regex screen, 6 categories, emits review files
  (precision to be established by eyeball, not assumed).

## 2026-07-28 — grounding in vector-space posts
- Read intent-extraction, perplexity-was-right-to-kill-ads, the-last-signal,
  ask-first, the-price-of-relevance.
- Design correction: sufficiency = yield of the SHIPPED intent-extraction
  prompt (sdk-web/src/intent.ts; provider-phrased sentence, NONE guardrail,
  no demographics) embedded with BGE-small-en-v1.5 — not an abstract
  attribute checklist. The study measures the deployed mechanism.
- Denominator = the "low tap rates / reach" risk Ask First already names.
  This number is the answer to a question the series asked in February.
- Phase plan: regex screen (recall) → manual review → run intent prompt on
  commercial subset → NONE-rate + extraction-yield = sufficiency.

## 2026-07-28 — regex screen fails, prompt promoted to classifier
- Sample landed: 1,993 conversations (20 offsets × 100, public view).
- Regex screen: 5.2% flagged, but precision on eyeball is near zero for
  "travel" (78/104 hits) — WildChat is dominated by content-AUTHORING
  requests (essays, roleplay, homework), so commercial keywords appear
  inside text being written, not needs being expressed. "book" as noun.
- Finding worth keeping: first-person need vs third-person content is THE
  discrimination problem for chat ad matching; a naive match-on-the-question
  network shows ads against essay prompts. The shipped prompt's NONE
  guardrail + "person could benefit from a professional service" framing is
  the discriminator. Regex demoted to cautionary baseline.
- extract_intent.py: verbatim INTENT_PROMPT from sdk-web/src/intent.ts,
  ollama llama3.2:3b, temp 0, first 3 user turns ≤4k chars, resumable.
  Running n=400.

## 2026-07-28 — instrument validity, twice
- llama3.2:3b run (n=400): 79% non-NONE, INVALID — model task-hijacks
  (does the user's request instead of extracting), drifts language, echoes
  user content into the "position sentence". Capability floor finding: below
  it the no-demographics guardrail fails silently and the extractor leaks
  conversation content into the embedded string. Kept as evidence.
- claude -p haiku run (n=60): 97% non-NONE, INVALID — used
  --append-system-prompt, so extractions ran inside the Claude Code agent
  harness (answered as a coding assistant, referenced this very project).
  Archived as intent_claude_haiku.INVALID-append-harness.jsonl.
- Fix: --system-prompt (full replacement) verified with PONG test. Rerunning.
- Meta: two runs, two construct-validity failures of our own instrument
  before any number is real. This is the post's methods section writing
  itself: grader-auditing discipline applied to one's own measurement.

## 2026-07-28 — wrapped-transcript fix measured; first real numbers
- Haiku clean run (n=60, --system-prompt): 20 flagged, but ~6 genuine; ~8
  task-hijacks (model does the user's task), rest refusal-text. Fidelity ~75%.
- Wrapped variant (same 60, transcript demoted to DATA in <transcript> tags):
  hijacks 8 → 0. Two former hijacks became CORRECT extractions (technical
  translation; social-content strategy). 9 intent / 51 NONE / 1 refusal-text.
- First denominator estimate: ~15% (9/60) of WildChat conversations yield a
  professional-service position sentence under the shipped prompt once
  fidelity is fixed. n=60 → CI is wide (~7-27%); scale next.
- Actionable SDK fix, receipt-backed: sdk-web/src/intent.ts passes raw
  conversation as the user message; imperative content hijacks extraction.
  Wrapping transcript as data eliminates it on this sample. Propose upstream.
- Residual: refusal-prose instead of NONE on policy-violating convos (1/60);
  correct instinct, wrong format; a "respond NONE even if content is
  objectionable" line would close it.
