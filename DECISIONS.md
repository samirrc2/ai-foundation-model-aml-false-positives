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
Projected pilot cost: 4 models × 2 variants × 2 seeds × 240 cases = **7,680
calls**; at ~400 input + ≤256 output tokens on mini/flash pricing, worst-case
≈ **$1–2**, comfortably < $10. The ledger still hard-aborts at $10 regardless.

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
