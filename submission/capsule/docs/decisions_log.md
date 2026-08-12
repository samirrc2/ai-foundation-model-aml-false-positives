# DECISIONS.md — P4 (append-only)

Every judgment call made without asking the researcher is logged here with its
rationale, so the preregistration stays clean and the choices are auditable.
**Append only. Do not rewrite prior entries.**

---

### 2026-07-15 · D1 — Directory is `Paper 4/`, not `Paper 5/`
The build prompt's ASCII tree header reads `Paper 5/` and its prose says "create
under `Paper 4/`". The working folder is explicitly `NIW/Paper 4/`. Resolved:
build everything under **`Paper 4/`**. Treated the `Paper 5/` label as a
copy-paste artifact from a sibling paper's spec.

### 2026-07-15 · D2 — Pilot model subset (cheap, 2 families × 2 variants)
Pilot registry = **4 cheap models, 2 within-family pairs**:
- OpenAI: `gpt-4o-mini`, `gpt-4.1-mini`  (within-family pair #1)
- Google: `gemini-2.0-flash`, `gemini-2.0-flash-lite`  (within-family pair #2)

Rationale: two families × two variants lets the pilot estimate **within- vs
cross-family** correlation cheaply (criterion 3 of the pilot gate) while staying
firmly in the mini/flash price tier. **All flagship models are excluded from the
pilot registry** (`pilot: false`) and reserved for the full run. xAI **Grok** is
full-run only and priced conservatively so the full-run cap bites early.

**Snapshot strings are provisional** and MUST be confirmed by `capture/probe.py`,
which records the *served-model fingerprint* + per-call price into a probe
receipt before any real run. If a snapshot 404s at probe time, swap to the
current mini/flash snapshot and log a follow-up decision. (The analysis is
agnostic to the exact snapshot; provenance is captured per row.)

### 2026-07-15 · D3 — Battery size & class balance
Pilot battery = **240 cases** (120 suspicious / 120 benign), stratified across
8 typologies × 3 difficulty levels. Full battery = **600 cases**, of which the
pilot 240 is a strict seeded stratified subsample (so pilot ⊂ full, same hashes
per case). Class balance **50/50** with benign cases deliberately built as **hard
negatives** (legitimate patterns that superficially resemble alerts) so a
flag-everything model cannot trivially pass. Difficulty mix ≈ 30% easy / 40%
medium / 30% hard.

Rationale: 120 suspicious cases give a usable denominator for per-model miss
rates and a joint-miss estimate with a finite bootstrap CI at pilot scale, while
keeping cost ≪ $10 (projected < $1 worst-case; see D6).

### 2026-07-15 · D4 — Exact flag mapping and miss unit
Constrained JSON `{"suspicious": bool, "typology": str|null, "rationale": str}`.
`flag = (suspicious==true)`. **Miss** = suspicious-labeled case returned
`no_flag`. Per-(model,case) miss indicator = **modal** replicate decision across
seeds × prompt variants, **ties broken toward flag** (conservative: never
over-count misses). ERROR replicates excluded from the vote; all-ERROR
(model,case) is NA and excluded from that model's marginal and any joint product.
Rationale: modal-at-case is the natural unit for cross-model correlation and for
clustering by typology; tie-to-flag makes the miss estimate conservative (biases
*against* the paper's own claim).

### 2026-07-15 · D5 — Independence-null formulation
Null: independent per-model errors ⇒ `J_ind(M) = ∏_m p_m` (product of marginal
miss rates). Claim: `J_obs > J_ind`, i.e. `R = J_obs/J_ind > 1`. Inference =
**cluster bootstrap resampling typologies** (the exchangeable unit), seeded, 2000
draws, 95% percentile CI; the test is whether the CI on `R` excludes 1.
Rationale: the product-of-marginals null is the standard homogenization/systemic-
failure benchmark (Bommasani 2022); clustering on typology avoids understating
uncertainty from within-typology structural similarity.

### 2026-07-15 · D6 — Pilot budget = $10 hard cap; projection
`BUDGET_PILOT = $10.00`, enforced by a per-model priced ledger with worst-case
pre-reservation under concurrency and a pre-flight projected-cost refusal.
`BUDGET_FULL = $200.00`, untouched until explicit go-ahead.
Projected pilot cost: 4 models × 2 variants × 2 seeds × 240 cases = **3,840
calls**; at ~400 input + ≤256 output tokens on mini/flash pricing, worst-case
≈ **$0.5–1**, comfortably < $10. The ledger still hard-aborts at $10 regardless.
(Confirmed by the offline dry-run: 3,840 rows captured, 0 ERROR.)

### 2026-07-15 · D7 — Prompt variants
Two pilot variants, both **supervisory**: `v_terse` (a compliance-officer one-liner
+ the JSON schema) and `v_fatf` (a short FATF-typology-aware instruction + schema).
Both forbid free-text outside JSON. Rationale: two variants give prompt-robustness
of the headline at pilot scale without multiplying cost; neither variant coaches
evasion (dual-use rule). Full run adds a third variant.

### 2026-07-15 · D8 — Seeds
`SAMPLING_SEED = 20260715` (battery generation + stratified subsampling),
`ANALYSIS_SEED = 4242` (bootstrap). Capture per-cell seed derived deterministically
from (case, prompt_variant, seed_index) via SHA-256, mirroring Paper 2's
cell-parity seed so every model sees identical seeds at a matched cell (the model
is the only difference driving cross-model correlation). Pilot uses seed indices
{0,1}.

### 2026-07-15 · D9 — Mock screener design (PILOT_MOCK=1)
The offline fake screener is deterministic in (model, variant, seed, case) and is
built to exhibit BOTH a measurable base rate (target pooled miss ≈ 25–40%) AND
correlated misses (shared per-case latent "hardness" ⇒ joint-miss > independence),
so the dry-run exercises the entire PASS/analysis path and demonstrates a
plausible signal. This is a *pipeline* validator, not a scientific result; real
numbers come only from live capture. Logged so no one mistakes mock output for
findings.

### 2026-07-15 · D10 — Serialization precedent
Transaction sub-networks are serialized in a fixed plain-text node/edge schema
following the graph-serialization convention of arXiv 2507.14785 (In-Context
Learning for Money-Laundering Detection in Financial Graphs), cited as precedent.
Rationale: reuses an established LLM-readable AML graph format; keeps the object
citable and avoids inventing an idiosyncratic encoding.

### 2026-07-16 · D11 — Pilot second family: xAI grok-4.5 (Gemini credits depleted)
At probe time the OpenAI pair returned clean, but BOTH Gemini keys failed with
`429 RESOURCE_EXHAUSTED — prepayment credits are depleted` (a billing issue on the
Google project, not a code/snapshot issue). The pilot must have a second foundation
family to compute the within- vs cross-family contrast (gate criterion 3), so the
Gemini pair was replaced in the **pilot** subgrid by a single xAI model. Per
docs.x.ai (2026-07-09), grok-3 and grok-3-mini were retired 2026-05-15; the current
general text model is **grok-4.5** ($2/$6 per 1M). Priced conservatively at $2.5/$7.

Consequences:
- Pilot models are now `openai_4o_mini`, `openai_41_mini`, `xai_grok(grok-4.5)` —
  2 families, within-family pair from OpenAI, cross-family pairs OpenAI×xAI. Only
  ONE xAI model is used to keep cost ~$2-3 (well under the $10 cap).
- grok-4.5 is technically flagship-tier, a deliberate exception to the "cheap-only
  pilot" rule forced by Gemini being unavailable; the $10 hard cap still binds and
  the projected cost is ~$2-3. `xai_grok.pilot` set true so the loader guard admits it.
- Gemini entries remain in the registry and the FULL subgrid; re-add
  `gemini_flash`/`gemini_flash_lite` to the pilot subgrid once the Google project is
  funded. The mock dry-run re-verified PASS with the new 3-model pilot.

### 2026-07-16 · D12 — Gemini billing restored → reverted to the cheap 4-model pilot
The researcher funded the Google project, so the pilot reverts to its original
cheap-only design: `openai_4o_mini`, `openai_41_mini`, `gemini_flash`,
`gemini_flash_lite` (two within-family pairs). grok-4.5 returns to **full-run only**
(`pilot: false`), now carrying `reasoning_effort: low` and `max_tokens: 512` so its
default reasoning does not exhaust the output budget. The agent gained
`reasoning_effort` support (injected for OpenAI-compatible providers, dropped on
"unsupported" errors). Net effect on the pilot: identical to the pre-registered
design; projected pilot cost well under $1 (all mini/flash). D11's substitution is
superseded but retained for the record.

### 2026-07-16 · D13 — Gemini flash snapshots retired → use current model aliases
After billing was restored, `gemini-2.0-flash-001` / `gemini-2.0-flash-lite-001`
returned **404 NOT_FOUND** — Google shut down the Gemini 2.0 Flash line on
2026-06-01. Updated the pilot Gemini pair to the current flash tier:
`gemini-flash-latest` (Gemini 3.5 Flash, GA 2026-05-19) and `gemini-flash-lite-latest`
(Gemini 2.5 Flash-Lite). Full-run `gemini_pro` → `gemini-pro-latest`. Rationale:
the `-latest` aliases resolve to the current stable release and cannot silently
404; reproducibility is preserved because `probe.py` records the served-model
fingerprint per receipt and every capture row carries its api_model + content hash.
Prices set conservatively (probe overwrites with measured). This is precisely the
provisional-snapshot risk the probe step exists to catch (models.yaml header note).
Sources: ai.google.dev/gemini-api/docs/models; changelog.

### 2026-07-16 · D14 — Gemini JSON parse errors → schema-constrained decoding + parser salvage
First real pilot capture: OpenAI models 0 ERROR; Gemini 3.5 Flash produced a 6.46%
ERROR rate, all `parse: Expecting ',' delimiter` — the model left an UNESCAPED quote
inside the free-text `rationale`, breaking otherwise-valid JSON. freeze.py correctly
refused (>2% ERROR → non-authoritative). Two fixes, neither changes the estimand or
the decision rule:
1. **Fix at the source:** Gemini calls now use schema-constrained decoding
   (`response_schema=_GeminiVerdict`), which forces valid JSON with correctly escaped
   strings. Best-effort: falls back to plain JSON mode if the installed SDK/model
   rejects the schema.
2. **Harden the parser:** if any provider emits malformed JSON, `parse_strict`
   recovers the VERBATIM `suspicious` boolean (and typology if cleanly present) by
   regex; it never invents a decision — if the boolean isn't literally present it
   still raises → ERROR. The salvaged decision is exactly what the model output.
Rationale: the flag is unambiguous even when a rationale quote breaks the JSON;
recording such a call as ERROR would understate real screening decisions. ERROR
remains first-class for genuinely unparseable/failed calls. Re-run the pilot fresh
(`RESET=1`) so all rows come from this code version; expected Gemini ERROR ≈ 0.

### 2026-07-16 · D15 — Pilot v1 KILL (0% miss) → Amendment 1 (external-standard hardening)
Pilot v1 on the real APIs ran clean (0 ERROR, $0.89) but returned pooled miss =
0.000 → `PILOT: KILL (criterion 2)`. Root cause: a construct-validity leak — the
serialization's `CONTEXT:` line stated the typology in plain English (an answer
key), and amounts/timing were unrealistically uniform. Response, per the
researcher's integrity framing:
- **Ordering as the control:** wrote `PREREGISTRATION_AMENDMENT.md` FIRST with an
  external-standard hardening spec (H1 raw logs only; H2 irregular sub-threshold
  amounts; H3 signal interleaved with benign background volume; H4 realistic
  temporal dispersion) derived from FATF red-flag indicators + SAML-D structure,
  with NO reference to model performance — THEN regenerated the battery from it.
  One pass only; no battery↔model iteration (that would be evasion/p-hacking).
- **Bounds:** analysis now reports pooled/per-model 95% upper bounds
  (Wilson + rule-of-three) so a second near-zero sweep is a quantified feasibility
  finding, plus the correlation-feasibility corollary.
- **Outcome pre-committed** (A4) before the re-run: band→PASS+freeze; <10% (incl.
  bounded ~2-3%)→feasibility KILL→T4-A "From Flips to Dollars" swaps in as P4;
  >70%→degenerate KILL.
- v1 KILL evidence preserved under `pilot/v1_KILL/` and `data/raw/v1_archive/`.
- New hardened battery hash in `manifest/battery_manifest.json`. Mock pipeline
  re-verified green on the hardened battery ($0). Real re-run pending on the
  researcher's machine.

### 2026-07-16 · D16 — Trimmed confirmatory full-run grid (cost < $25, lit-calibrated)
The pivot paper's confirmatory full run was priced at ~$42 (7 models × 3 variants ×
3 seeds × 600). Trimmed to **2 variants × 2 seeds** (keeping all 7 models + 600
cases) → **~$18.8 realistic, worst-case $21.2, cap set to $25**. Rationale: the
headline estimand is *cross-model* FP variance, so **model breadth is what must be
preserved** — 7 models (mini→flagship, 3 families) already exceeds the published
AML-LLM norm (single-model case studies get accepted, e.g. arXiv 2507.14785;
comparative benchmarks run 1–13). Seeds/variants are robustness dimensions and were
economized to 2 each (still above the common single-run norm), and aligns with the
program's ~$15 cap precedent (Paper 2). Also lowered chat `max_tokens` 256→128 and
grok 512→256 (observed output ≈45 tok) so the worst-case reservation fits under the
$25 cap without a preflight refusal. Pre-data change → not p-hacking.

### 2026-07-16 · D17 — Drop gemini_pro from the full grid (thinking-mode incompatibility + cost)
Full-run probe: 6/7 models OK; `gemini-pro-latest` returned `400 INVALID_ARGUMENT:
"Budget 0 is invalid. This model only works in thinking mode."` — Gemini Pro is a
forced-thinking reasoning model and rejects the thinking-disabled config used for
Flash. Two changes: (1) **Code fix** — `thinking_budget` is now a per-model field;
set only when declared (`0` disables thinking for Flash/Flash-Lite; omitted = model
default so a thinking-required model works). (2) **Design** — dropped `gemini_pro`
from the full subgrid: a forced-thinking model emits costly reasoning tokens
($10/1M out) and is not a realistic high-volume transaction-screening deployment;
flagship diversity is preserved by gpt-4o + grok-4.5 across two other families.
Full grid now **6 models × 2v × 2s × 600 = 14,400 calls, ~$14 realistic, worst-case
$16.6, cap $25**. gemini_pro stays in the registry (pilot:false) with correct
thinking config for optional later use. The user's interrupted run used a stale
(pre-trim) config and spent $0.

### 2026-07-16 · D18 — Cross-provider parallelism + two capture bugs fixed
The first full-run attempt surfaced three issues, all fixed:
1. **freeze wrong file** — `run_all.sh` didn't pass `--subgrid` to `freeze.py`, so it
   froze `runs_pilot_*` instead of `runs_full_*`. Fixed.
2. **Permanent key benching → 429 cascade** — a rate-limited key was benched for the
   whole run; a burst knocked out all 3 OpenAI keys and every call then ERRORed.
   Benching is now **temporary** (30s cooldown, key auto-recovers); the orchestrator
   treats "all keys cooling down" as a retryable wait (up to MAX_RETRIES), so a
   rate-limit burst pauses and resumes instead of erroring.
3. **No cross-provider parallelism** — `run_all.sh` ran models strictly sequentially,
   so 5 workers piled onto ONE provider (causing the 429s) while others sat idle.
   Rewritten to run **one background stream per provider** (OpenAI ‖ Google ‖ xAI),
   each with independent rate limits, its own ledger file (`_<provider>`), and a
   sub-cap = BUDGET/num_providers (so the global $25 cap is preserved). Models stay
   sequential *within* a provider (concurrent same-provider workers were the problem).
   Verified end-to-end in MOCK on the full subgrid ($0, 3 parallel streams clean).

### 2026-07-16 · D19 — Drop xai_grok (account out of credits) → final grid = 5 models
Mid-run, xAI returned `403 permission-denied: "team ... used all available credits
or reached its monthly spending limit"` — a terminal account block, not a rate
limit. Code hardened: classify_error now detects account-exhaustion (spending
limit / permission-denied / billing) and the orchestrator halts that provider's
stream cleanly instead of erroring every cell. Decision (researcher): **drop grok**
rather than buy more credits (third credit wall after Gemini ×2). Final full grid =
**5 models across 2 families** (OpenAI: 4o-mini, 4.1-mini, 4o; Google: flash,
flash-lite), 2v × 2s × 600 = 12,000 calls, **~$8 realistic**, 2 parallel streams
(cap $12.50 each, global $25). The FP-variance headline is already large within
these (pilot 0%→80%); 5 models exceeds the AML-LLM norm. grok + gemini_pro stay in
the registry for an optional one-model top-up if a reviewer asks for a 3rd family.
