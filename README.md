# intent-sufficiency

Do chat conversations contain enough declared intent to match ads without a user
dossier? This project measures that on real conversations (WildChat-1M, public).

## The claim under test

Chat-ad targeting quality is assumed to require user profiles (OpenAI targets on
"past chat history and previous ad interactions"). The counter-claim: in chat,
declared intent dominates the dossier — the conversation itself carries the
attributes a matcher needs, so profile targeting adds lift only on a residual.

What this repo actually measures (scoped after external review):
1. **Extraction yield** (public data, here): the share of conversation
   *prefixes* (first 3 user turns, ≤4k chars, assistant turns removed) where
   a *repaired* version of the [Intent Extraction]
   (https://june.kim/intent-extraction) prompt — transcript wrapped as data;
   the shipped unwrapped prompt fails fidelity materially (see worklog) —
   returns a service-position sentence instead of NONE. This is
   prompt-specific professional-service yield, not commercial-intent
   prevalence: the prompt excludes products/retail/travel inventory and can
   nominate services for users with no purchase intent. Ground-truth human
   labels (precision AND false-NONE rate) are planned, not done; until then
   the extractor partially defines the construct it measures.
2. **Dossier redundancy** (public data, here): for users (approximated by
   hashed_ip — shared/dynamic IPs make this imperfect) with prior
   conversations, does adding prior history change the extracted intent,
   in excess of the extractor's own run-to-run disagreement (control arm:
   question-only run twice)? Estimand: per-user, one non-first target each.
   English-only; a different population than the multilingual yield sample.
3. **Matchability** (planned, not implemented): embed extractions against an
   advertiser catalog (BGE-small-en-v1.5, the SDK's model) and show distance
   distributions.
4. **Delta** (needs live traffic, NOT this repo): CTR/RPM of question-only vs
   question+profile matching. Public data has no outcomes; a judged proxy
   would be mark-to-model and is out of scope on purpose.

Corpus caveat: WildChat is public-share-selected ChatGPT-mirror traffic
(heavy on content-authoring, homework, roleplay, jailbreaks) served through
the ungated 837,989-row public view. "Real conversations," not "representative
consumer-assistant traffic."

Pre-registration: predictions and thresholds were committed and pushed before
either run launched — commit `880619f`, pushed 2026-07-28, externally
timestamped on GitHub.

Demand-side prior: [The Last Signal](https://june.kim/the-last-signal) (via Don
Marti) argues surveillance targeting carries no quality signal; this repo
measures the supply-side complement — how much matchable intent the
conversation volunteers without any profile.

## Data

WildChat-1M (allenai/WildChat-1M), fetched via the HuggingFace datasets-server
rows API — no auth, reproducible by anyone. Learning-scale sample first
(~2,000 conversations); scale later if the instrument holds.

## Method discipline

- Deterministic first: keyword/regex commercial-intent screen, then manual
  review of a stratified sample before any model-based labeling.
- Every number in results/ traces to a script in src/ and a cached raw sample
  in data/ (content-addressed by fetch parameters).
- No performance claims from judged relevance. Sufficiency is a property of
  the text; performance is a property of outcomes we don't have here.

## Status

See worklog.md.

## License

[AGPL-3.0](LICENSE). Data samples derive from
[WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M) (AI2 ImpACT
license); the fetch script reproduces them from the public API rather than
redistributing the corpus.

## Data pointers

The corpus is not redistributed; the repo commits exact pointers instead:
`data/MANIFEST.json` (fetch parameters + the 1,993 `conversation_hash` ids,
sufficient to reconstruct the identical sample from the public API) and
`results/labels_*.json` (per-run outcome labels keyed by hash, so every
reported rate is checkable row-by-row against a reconstruction).
