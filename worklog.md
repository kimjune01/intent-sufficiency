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

## 2026-07-28 — pre-registration (before scale-up and dossier runs)
Predictions, stated before running, thesis at stake:
1. Full-sample wrapped extraction (n=1993, haiku): non-NONE rate lands in
   10-20% (pilot: 9/60 = 15%). Below 5% would undercut the reach story;
   above 30% would suggest the NONE gate is leaking.
2. Dossier-redundancy: for users with ≥2 conversations, adding the user's
   OTHER conversations as history changes the extracted intent materially
   (cosine < 0.85 between question-only and history-conditioned position
   sentences, BGE-small) in <20% of cases, and flips NONE→intent in <10%.
   If history changes the match in a large fraction, the declared-intent-
   dominates-the-dossier thesis takes real damage and the post must say so.
Design notes: hashed_ip links users in the public view; identifiers stay
local (data/ is not committed), published results key on conversation_hash.

## 2026-07-28 — dossier-redundancy results (n=80 users, pre-registered)
- material change 11/80 = 13.8% (< 20% predicted ✓); none→intent 8.8% (< 10% ✓)
- Composition is the story:
  * 76% both-NONE (casual either way — consistent with ~15% denominator)
  * Of the 12 conversations that declare intent question-only: 8 unchanged,
    2 changed but same-neighborhood (cos 0.837/0.842, just under the strict
    0.85 bar; eyeball: same-domain refinements), 2 suppressed to NONE
    (likely extraction instability — flag, don't spin).
  * The dossier's whole contribution concentrates in none→intent (7 cases):
    history surfaces intent when the CURRENT conversation is casual. That is
    reach into the non-consented surface — exactly the inventory the
    Ask First two-phase model refuses by design (no commercial context, no
    indicator). Within the consented surface, the dossier is ~redundant.
- Caveats for the post: n=80; hashed_ip≈user is approximate (shared IPs);
  extraction nondeterminism bounds the small buckets; single corpus.

## 2026-07-28 — codex review volley 1: v1 dossier result WITHDRAWN
34-item external review. Accepted as invalidating v1's treatment: history
included FUTURE conversations (temporal leakage); the guard told the model to
ignore the history whose effect we measured; no nondeterminism control, so
all 11 "material changes" are confounded with run-to-run variance; NONE→intent
conditional denominator is 7/68 = 10.3%, breaching the pre-registered <10%
under that reading; 13.8% has a 95% CI of ~7-23%, so "prediction held" was
too strong; "cosmetic changes" was a post-hoc override of the registered
threshold. v1 numbers are not to be cited. v2 fixes: prior-only history,
history-may-inform guard, q1/q2 control arm, sanitized tags, validity
classification (ERROR/empty/malformed no longer count as intent), per-run
config header, actual included-history counts. README rescoped: yield ≠
commercial-intent prevalence; wrapped prompt is a REPAIRED mechanism, not the
shipped one; matchability step marked planned, not done. Rebutted: prereg
immutability — commit 880619f was pushed before either run launched.

## 2026-07-28 — dossier v2 results (control-adjusted, n=80)
- CONTROL (q1 vs q2, identical condition): disagreement 11/80 = 13.8% —
  exactly the rate v1 reported as its treatment effect. v1's headline was
  the extractor's own noise, fully.
- TREATMENT (q1 vs prior-only history): 13/79 = 16.5%.
- EXCESS = +2.7pp, n=80 → not distinguishable from zero. One clearly real
  dossier override (cos 0.49: translation → financial recovery planning).
- Directional read: at this instrument's noise floor (~14% self-disagreement
  at CLI default temperature), adding a prior-history dossier moves extracted
  intent by an amount we cannot separate from noise; what signal exists sits
  in none→intent (8 vs control 6), direction consistent with "reach, not
  accuracy." Weak result, expected, in scope.
- Instrument lesson: control-arm cosines dip to 0.842 — self-disagreement
  crosses the 0.85 bar, so ANY threshold-based change metric without a
  control arm overstates. To detect small effects: k-vote extraction or
  pinned temperature to lower the floor first.

## 2026-07-28 — codex volley 2: three fixes, then convergence
Codex pass 2 cleared the revised account except: (1) tied-timestamp subject
counted as treated with zero history — fixed, common analysis set n=78;
(2) no paired test — added exact McNemar on discordant pairs; (3) wording
overreach on "only visible signal" — adopted codex's phrasing. Final numbers:
control 11/78 = 14.1%, treatment 13/78 = 16.7%, excess +2.6pp, discordant
7 vs 5, McNemar p = 0.774. Blog-post sentence (codex-agreed): "Adding prior
conversation history changed extracted intent only about 2.6 percentage
points more often than a repeat extraction without history; at n=78 that
descriptive difference is too imprecise to interpret as a dossier effect.
The observed asymmetry toward NONE→intent with history (8 vs 6) is
exploratory." Convergence: no remaining computational defects; scope items
are conceded limitations of a directional study.
