# PREREGISTRATION — P4 · "One Screener to Miss Them All"
### Foundation-model monoculture in LLM anti-money-laundering (AML) screening

**Status:** FROZEN (day-1). **Frozen date:** 2026-07-15.
**Framework cell:** B9 — systemic risk / correlated failure (measured).
**Do not edit after freeze.** Deviations are logged in `PREREGISTRATION_AMENDMENTS.md`
(created only if needed) and in `DECISIONS.md`; the frozen text here is the contract
against which the pilot and full run are judged.

> This document fixes, before any API spend: the estimands, the battery
> specification, the exact flag-mapping and "miss" definition, the independence
> benchmark and its test, the **pilot gate** (three PASS criteria) and the stop
> rules, and the conditional full-run design. Every headline number the paper
> will cite is produced by `analysis/run.py` into `claims.json`, tagged with the
> config hash that produced it.

---

## 0. One-paragraph claim

On a FATF/SAML-D-anchored **synthetic** typology battery, we run *K* foundation
models × seeds × prompt variants as AML transaction-screeners and measure two
things: (1) the **joint-miss probability** — the chance that *every* model in a
set fails to flag the *same* truly-suspicious case — relative to an
**independence benchmark** (the product of the models' marginal miss rates); and
(2) the **defense-in-depth recovery rate** — the fraction of the miss-reduction
that a *heterogeneous* second screening line is *promised* (under independence)
that it *actually delivers* once model errors turn out to be correlated. The
paper's signal is: joint-miss probability **significantly exceeds** the
independence benchmark **AND** second-line recovery is **materially < 100%**.

We **measure misses; we never optimize evasion** (dual-use discipline, §7). The
framing is supervisory throughout.

---

## 1. Estimands (frozen)

Let the battery contain suspicious cases indexed by *c* ∈ 𝒮 (ground-truth
label = suspicious). For each model *m* and case *c*, capture yields a set of
replicate decisions across seeds × prompt variants; define the **per-cell miss
indicator** `miss[m,c] ∈ {0,1}` by the modal-decision rule in §3. Let
`p_m = mean_c∈𝒮 miss[m,c]` be model *m*'s **marginal miss rate**.

### Primary estimand — joint-miss probability ratio vs independence
For a model set **M** (headline: the full pilot/full model set):

- **Observed joint-miss** `J_obs(M) = mean_c∈𝒮 ∏_{m∈M} miss[m,c]`
  (fraction of suspicious cases *every* model in **M** misses).
- **Independence-predicted joint-miss** `J_ind(M) = ∏_{m∈M} p_m`.
- **Primary estimand:** the **joint-miss ratio** `R(M) = J_obs(M) / J_ind(M)`.

**Direction of the whole paper:** `R(M) > 1` (misses are positively correlated;
monoculture). The paper's quantitative contribution is the *magnitude* of `R`
with a CI, not the mere existence of correlation.

### Secondary estimand — defense-in-depth recovery rate
Two-line system = a **primary** screener *P* backed by a **second-line** screener
*S*. The composite misses a suspicious case only if *both* miss it.

- Promised residual (independence): `res_ind = p_P · p_S`.
- Promised reduction from the single-line rate: `red_ind = p_P − p_P·p_S = p_P(1 − p_S)`.
- Observed residual: `res_obs = mean_c∈𝒮 (miss[P,c]·miss[S,c])`.
- Observed reduction: `red_obs = p_P − res_obs`.
- **Recovery rate** `ρ(P,S) = red_obs / red_ind` (clamped for reporting to
  `[−∞, 1]`; `ρ = 1` ⇔ the second line delivers exactly what independence
  promised; `ρ < 1` ⇔ correlation ate part of the promised protection;
  `ρ ≤ 0` ⇔ the second line added no net protection).

Headline recovery = the mean of `ρ(P,S)` over **heterogeneous** (cross-family)
(P,S) pairs; reported alongside the **homogeneous** (within-family) mean as the
contrast that isolates the monoculture effect.

### Supporting estimands
- **Pairwise chance-corrected agreement on misses** over 𝒮: Cohen's **κ**
  (headline), plus **Scott's π** and **Gwet's AC1** (robustness — §6; the same
  three-statistic panel as Paper 2). Reported as a K×K matrix and as
  within-family vs cross-family means.
- **Systemic-failure ratio** (Bommasani et al., NeurIPS 2022 homogenization
  metric): `SFR = J_obs(M) / J_ind(M)` for the full set (numerically the primary
  `R(M)`; reported under the Bommasani name to connect to the homogenization
  literature).
- **Within-family vs cross-family correlation contrast:** mean pairwise κ (and
  mean pairwise joint-miss ratio) among model pairs *sharing a provider family*
  minus the same among pairs *spanning families*. A positive contrast =
  provider-level architectural sharing drives correlation; a large *cross-family*
  correlation is the stronger monoculture claim (shared failure even across
  vendors).

---

## 2. Battery specification (frozen)

**Provenance & anchoring.** Typologies are drawn from the **FATF** published
typology catalogue (structuring/smurfing, layering, trade-based ML, cash-intensive
fronts, funnel accounts, mule networks, shell layering, rapid movement /
pass-through) and the **SAML-D** / **IBM AMLSim** synthetic-AML lineages. Cases
are **synthetic** and generated **deterministically offline** ($0). The
transaction-graph serialization convention follows the format used by *In-Context
Learning for Money-Laundering Detection in Financial Graphs* (arXiv 2507.14785),
cited as precedent for LLM-readable graph serialization.

**Object.** Each case is a serialized description of a small transaction
sub-network (accounts/entities as nodes, transfers as edges with amounts, dates,
directions, and light KYC/context annotations), rendered in a fixed plain-text
schema. A screener reads one case and returns a constrained JSON verdict (§3).

**Labels.** Each case carries a ground-truth label:
- `suspicious` — the sub-network instantiates a recognized laundering typology
  (carries a `typology` tag: `structuring`, `layering`, `trade_based`,
  `mule_network`, `shell_layering`, `funnel_account`, `rapid_passthrough`,
  `cash_intensive_front`).
- `benign` — a plausible legitimate pattern that *superficially resembles* an
  alerting condition (e.g. payroll fan-out, treasury sweeps, genuine trade
  finance, high-volume retail settlement) — i.e. **hard negatives**, so a "flag
  everything" model does not trivially score well.

**Difficulty spread.** Each case has a `difficulty ∈ {easy, medium, hard}` knob
that controls how salient the typology signature is (amount structuring just
under/over reporting thresholds, number of hops, obfuscation via intermediaries).
Difficulty is a *design* attribute used for stratified sampling and dose-response
reporting; it is **not** tuned against any model (no evasion search — §7).

**Class balance.** Target **50% suspicious / 50% benign** overall; suspicious
cases spread across the 8 typologies; difficulty spread ≈ 40% medium, 30% easy,
30% hard. Exact counts are emitted in the frozen battery manifest.

**Sizes.**
- **Pilot battery:** a **stratified subset of ~240 cases** (~120 suspicious,
  ~120 benign), balanced across typology × difficulty. (Range 200–300 permitted;
  exact N logged in `DECISIONS.md` and the battery manifest.)
- **Full battery:** the **whole battery, ~600 cases** (final N fixed at full-run
  time within 500–800, pre-registered here as "the whole battery"; the pilot
  subset is a strict, seeded stratified subsample of it).

**Freeze.** `build_battery.py` is deterministic (seeded). The battery is
**collect-once**, serialized to `data/battery/`, and **SHA-256'd**; the hash is
recorded in the manifest and referenced by every downstream artifact. The battery
is immutable once frozen; regenerating must reproduce the identical hash.

---

## 3. Ground truth, the screening call, and the exact "miss" mapping (frozen)

**The screening call.** Per **screening cell** = (model, prompt_variant, seed,
case): one call. The model is instructed to return **only** a constrained JSON
object:

```json
{"suspicious": true|false, "typology": "<one of the 8 tags>"|null, "rationale": "<=30 words"}
```

**Flag mapping.** `flag = (suspicious == true)`. `no_flag = (suspicious == false)`.
- Parsing is strict (JSON object extracted; booleans coerced only from a real
  JSON boolean or the exact strings `"true"/"false"`; `typology` validated
  against the tag set or null; rationale truncated to 30 words).
- A call that fails, times out, returns non-JSON, or violates the schema is
  recorded as **`ERROR`** — a **first-class label**, never silently coerced to
  flag or no-flag (§ stop rules).

**Miss (false negative) definition.** A **miss** is: a case with ground-truth
label `suspicious` for which the screener returns `no_flag`. Misses are defined
**only on suspicious cases**. (False *positives* — flagging a benign case — are
recorded and reported as a supporting operating-point statistic, but the paper's
estimands are about *misses*.)

**Per-cell (model, case) miss indicator** (the unit for correlation): aggregate
the replicate decisions for (model, case) across seeds × prompt variants by
**modal decision** (majority vote; ties broken toward `flag`, i.e. the
*harder-to-miss* / conservative resolution, so we never over-count misses).
`miss[m,c] = 1` iff the modal decision on a suspicious case is `no_flag`. A
replicate-level view (mean miss rate across replicates) is retained for the
noise-floor robustness report but is **not** the headline unit.

**ERROR handling in aggregation.** ERROR replicates are excluded from the modal
vote; if *all* replicates of a (model, case) are ERROR, that (model, case) is
`NA` and excluded from that model's marginal and from any joint-miss product
involving it (documented; counted). Capture with **> 2% ERROR overall is
non-authoritative** until re-run.

---

## 4. Independence benchmark and the test (frozen)

**Null.** Under the null of **independent** per-model errors, the probability that
all models in **M** miss the same suspicious case equals the product of their
marginal miss rates: `J_ind(M) = ∏_{m∈M} p_m`. The alternative (the paper's
claim) is `J_obs(M) > J_ind(M)`, i.e. `R(M) = J_obs/J_ind > 1`.

**Estimator & inference.** All headline quantities (`p_m`, `J_obs`, `J_ind`,
`R`, `ρ`, κ/π/AC1, the within/cross contrast) are computed by `analysis/run.py`.
Uncertainty is a **cluster bootstrap resampling the clustering unit = typology
stratum** (see §5), seeded (`ANALYSIS_SEED`), default **2000** draws, reported as
a 95% percentile CI. The primary test is whether the bootstrap CI on `R(M)`
excludes 1 (equivalently, whether the CI on `J_obs − J_ind` excludes 0). The
recovery-rate test is whether the CI on heterogeneous `ρ` excludes 1 from below.

**Why cluster on typology.** Cases within a typology share generative structure;
treating cases as independent would understate uncertainty. Typologies are the
exchangeable unit a referee would accept as "another draw of the world."

---

## 5. Pilot gate — the ≤ $10 spend wall (frozen, pre-registered)

**Nothing beyond the pilot runs until the pilot passes.** The pilot uses
**cheap models only** (mini/flash tier; any flagship — e.g. Grok, large GPT — is
excluded from the pilot registry and reserved for the full run).

**Budgets.**
- `BUDGET_PILOT = $10.00` — **hard**. The priced, per-model spend **ledger**
  aborts the run mid-flight the instant projected-or-actual cumulative spend
  crosses $10 (worst-case cost is *reserved* before each call under concurrency,
  so the cap is safe in parallel). **Pre-flight refuses to start** if the
  projected pilot cost > $10.
- `BUDGET_FULL = $200.00` — a **separate** cap, **not touched** until the
  researcher explicitly approves the full run after reading `PILOT_VERDICT.md`.

**Pilot PASS criteria (all three must hold):**

1. **Ran clean.** End-to-end, resumable, **0 ERROR** records (equivalently ≤ 2%
   ERROR and re-run to 0 for authority), total spend **≤ $10**.
2. **Measurable base rate.** Pooled per-model false-negative (miss) rate on the
   pilot battery lands in a **measurable band, 10%–70%**. If models catch
   everything (~0% miss) or miss everything (~100%), there is no variance to
   correlate → **KILL** (report why; do not spend more).
3. **Estimable correlation with signal.** Cross-model joint-miss probability is
   estimable with a **finite CI**, and its **point estimate > the independence
   benchmark** (`R > 1`, the direction of the whole paper). A **within-family vs
   cross-family** contrast is computable.

**Verdict.** If all three hold → print `PILOT: PASS → cleared for full run` and
**stop** for the researcher's go-ahead. If a measurability/variance criterion
fails → `PILOT: KILL (<criterion>)`. If an operational criterion fails →
`PILOT: FAIL (<criterion>)`. **Never auto-proceed to the full run.**

---

## 6. Robustness (native, not amended)

Pre-registered as part of the design (not post-hoc):
- **Three chance-corrected agreement statistics** — Cohen's κ, Scott's π,
  Gwet's AC1 — reported for every pairwise miss-agreement headline (as Paper 2).
  A finding that flips sign across these is flagged non-robust.
- **Prevalence-vs-churn decomposition of misses** — decompose cross-model
  disagreement on misses into a *prevalence* component (models differ in overall
  miss rate) and a *churn* component (models miss *different* cases at matched
  rates); the monoculture claim rests on the *co-incidence* of misses, so we show
  it survives conditioning on prevalence.
- **Noise floor** — replicate-level within-(model) disagreement (seeds ×
  variants) is reported as the floor against which cross-model co-miss is judged.
- **Prompt-variant sensitivity** — headline `R` and `ρ` recomputed per prompt
  variant; a finding driven by a single variant is flagged.

---

## 7. Dual-use discipline (hard design constraint, frozen)

We **measure** screening misses; we **never optimize evasion**. Concretely and
bindingly:
- **No arm** of this study searches for, ranks, or reports laundering text /
  transaction structures that *beat* a screener. Difficulty is a fixed design
  knob set from FATF typology salience, **not** tuned against model outputs.
- The battery is **synthetic** and typology-anchored; it is not a catalogue of
  working evasion recipes and is not published as one.
- Rationales and outputs are used only to compute flag/miss labels; we do not
  mine them for evasion guidance.
- Framing is **supervisory** throughout: the deliverable is a measurement of
  correlated blind spots for regulators/second-line designers, not an attacker
  tool. This constraint shapes the battery and the prompts and is restated in
  `README.md`.

---

## 8. Full-run design (conditional on pilot PASS; frozen targets)

Activated **only** on explicit go-ahead after `PILOT_VERDICT.md`:
- **Models (K):** pilot cheap set **+** a distinct **third family (xAI Grok,
  flagship)** **+** larger within-family variants (e.g. full-size GPT and Gemini
  Pro). ≥ 3 families so the cross-family monoculture claim spans vendors. Grok is
  the **cost driver** → priced **conservatively** so `BUDGET_FULL` bites early.
- **Battery (N):** the whole battery (~600 cases; §2).
- **Seeds:** ≥ 3 (from ≥ 2 in pilot). **Prompt variants:** ≥ 3 (from 2 in pilot).
- **Budget:** `BUDGET_FULL = $200`, same ledger machinery, same abort semantics.
- **Endpoints:** identical to the pilot (§1) so the pilot is a true dress
  rehearsal of the full analysis; the pilot's `claims.json` schema == the full
  run's.

---

## 9. Stop rules (verbatim, frozen)

- **Budget breach:** cumulative projected-or-actual spend > active cap
  (`BUDGET_PILOT` in pilot) ⇒ orchestrator drains in-flight workers and **stops**;
  the run is **resumable** (append-only; completed cells are never re-billed).
- **ERROR rate:** any capture with **> 2% ERROR** is **non-authoritative** until
  re-run; ERROR is never coerced to a flag/miss. `MAX_RETRIES = 10`, honoring
  `Retry-After`.
- **Base-rate out of band:** pooled miss rate ≤ ~10% or ≥ ~70% on the pilot ⇒
  **KILL** (no variance to correlate); report and stop.
- **No signal:** if `R ≤ 1` point-estimate or the joint-miss CI is not estimable
  ⇒ pilot **FAIL** on criterion 3; stop.
- **Provenance:** every API result persisted with (model, prompt hash, seed, case
  id, retrieved_at, content SHA-256); runs are **append-only** and never
  overwritten. Analysis reads **frozen** CSVs only and is byte-identical on
  re-run.

---

## 10. CAPTURE ↔ ANALYSIS wall (frozen)

- **CAPTURE** talks to live vendor APIs; it is impure, resumable, quota-aware,
  costs money, and **freezes + hashes** raw outputs the moment they land.
- **ANALYSIS** reads **frozen CSVs only**; it is pure, seeded, **byte-identical on
  re-run**, and costs **$0**.
- No analysis step may issue a network call or read an unfrozen CSV. This wall is
  the reproducibility guarantee and is identical in spirit to Paper 2.

---

*End of preregistration. Frozen 2026-07-15. Config hash and battery hash are
recorded in `manifest/` at build time and echoed into `claims.json`.*
