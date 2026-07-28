# intent-sufficiency

Do chat conversations contain enough declared intent to match ads without a user
dossier? This project measures that on real conversations (WildChat-1M, public).

## The claim under test

Chat-ad targeting quality is assumed to require user profiles (OpenAI targets on
"past chat history and previous ad interactions"). The counter-claim: in chat,
declared intent dominates the dossier — the conversation itself carries the
attributes a matcher needs, so profile targeting adds lift only on a residual.

Decomposition:
1. **Denominator** (public data, this repo): what share of real chat
   conversations carry commercial intent at all. This directly quantifies the
   documented open risk in [Ask First](https://june.kim/ask-first) ("high-intent
   queries may be the only viable inventory... it limits the model's reach") —
   the reach of the two-phase model on real traffic.
2. **Sufficiency** (public data, this repo): of those, what share yield a
   provider-position sentence under the [Intent Extraction]
   (https://june.kim/intent-extraction) prompt — conversation text alone, no
   demographics, NONE guardrail — that embeds (BGE-small-en-v1.5, the SDK's
   model) close to a plausible advertiser position. Sufficiency is measured by
   the shipped mechanism, not by an abstract attribute checklist.
3. **Delta** (needs live traffic, NOT this repo): CTR/RPM of question-only vs
   question+profile matching. Public data has no outcomes; a judged proxy would
   be mark-to-model and is out of scope on purpose.

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
