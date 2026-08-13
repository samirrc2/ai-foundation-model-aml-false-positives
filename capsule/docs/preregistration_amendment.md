# PREREGISTRATION AMENDMENT 1 — P4
### Hardened battery serialization (external-standard spec), power bound, and pre-committed outcome mapping

**Date:** 2026-07-16. **Amends:** `PREREGISTRATION.md` (frozen 2026-07-15).
**Status of the frozen prereg:** unchanged except where this amendment explicitly
says so. **What changes:** the battery *generation* (serialization + case
construction) only. **What does NOT change:** the estimands (§1), the pilot gate
and stop rules (§5, §9), the independence null (§4), the dual-use discipline (§7),
and the CAPTURE↔ANALYSIS wall (§10).

> **Ordering is the integrity control.** This spec is written **before** any case
> is regenerated, and every criterion below is derived from **external standards
> (FATF red-flag indicators; SAML-D case structure)** — *not* from what the pilot
> models got right or wrong. Cases are then regenerated to satisfy this spec. We
> make this change **once**; we do **not** iterate battery → inspect model outputs
> → re-harden. That loop would be evasion optimization / p-hacking and is
> forbidden by the frozen prereg §7. This is the single amendment.

---

## A0. Why an amendment at all (stated plainly, for the record)

Pilot v1 (frozen battery `data/battery/pilot.jsonl`, config hash recorded in
`manifest/`) returned a **pooled per-model miss rate of 0.000** across four models
(gpt-4o-mini, gpt-4.1-mini, gemini-flash, gemini-flash-lite), with low false
positives on the hard-negative benign cases → `PILOT: KILL (criterion 2)`. See
`pilot/PILOT_VERDICT.md`, `claims.json`.

Inspection of the v1 serialization revealed a **construct-validity defect**: every
serialized case ended with a natural-language `CONTEXT:` line that *stated the
typology in plain English* (e.g. *"Single beneficiary receives 9 sub-$10,000 cash
deposits within weeks"*). A screener reading that line is not performing
transaction screening — it is reading an answer key. This is a defect in the task
regardless of any model's score. The spec below removes it and brings the
remaining serialization in line with how AML transaction data actually presents,
using external references only.

**We commit, before regeneration, to publish whatever the hardened re-run
returns — including a second KILL — and to treat the outcome per the pre-committed
mapping in A3.**

---

## A1. Hardened case-construction spec (derived from FATF + SAML-D only)

Each criterion cites the external basis and is written without reference to model
behaviour.

**H1 — Raw transaction logs only; no natural-language summaries.**
The serialization presents nodes (accounts/entities with KYC/jurisdiction
attributes) and edges (transfers: amount, date, direction, channel) **only**. The
`CONTEXT:` summary line is **removed entirely**. *Basis:* real transaction-
monitoring alerts present structured transaction records; the analyst infers the
typology. SAML-D and IBM AMLSim distribute labelled transaction graphs, not
prose typology labels.

**H2 — Irregular sub-threshold amounts (no uniform tells).**
Structuring/funnel amounts are drawn from a realistic dispersed distribution
across the sub-reporting range (e.g. \$1,200–\$9,900) with mixed round and
non-round values and only a *minority* sitting just under the \$10,000 CTR line —
**not** a uniform cluster of near-identical \$9,500s. *Basis:* FATF structuring
red-flag indicators describe deposits *structured to avoid reporting thresholds*
across varied amounts and locations; a uniform just-under pattern is an artifact,
not a realistic signature.

**H3 — Typology signal interleaved with benign background volume.**
Suspicious sub-networks embed the typology transactions **among legitimate
background transactions** (payroll, vendor payments, routine transfers) on the
same accounts, so the laundering signal must be separated from noise rather than
appearing in isolation. Benign cases likewise carry realistic mixed volume.
*Basis:* FATF guidance emphasises that laundering is layered *within ordinary
business activity*; SAML-D injects illicit patterns into a background of normal
transactions.

**H4 — Realistic temporal dispersion.**
Transaction dates are dispersed over a realistic window with irregular spacing
(not all within a tight, obviously-clustered span), while preserving typology-
defining timing where the typology requires it (e.g. rapid pass-through remains
same-day). *Basis:* FATF timing red flags are about *pattern* (velocity,
round-tripping), not about every case sharing an identical short window.

**Unchanged:** the 8 suspicious typologies and 8 benign hard-negative patterns,
the labels, the class balance (50/50), the difficulty strata, the stratified
pilot⊂full construction, determinism + SHA-256 freeze, and the constrained-JSON
verdict contract. Only the *rendering and amount/time/volume construction* of
cases change, per H1–H4.

**New battery hash.** Regeneration produces a new battery; its SHA-256 is recorded
in `manifest/battery_manifest.json` and echoed into `claims.json`. The v1 battery
and its KILL remain on record; they are not overwritten in the paper's narrative.

---

## A2. Re-run design

Identical grid to the pilot (4 cheap models × 2 prompt variants × 2 seeds × the
240-case hardened pilot battery), same \$10 hard cap, same ledger and freeze
machinery. Cost ≈ the v1 pilot (~\$1). CAPTURE is re-run fresh (`RESET=1`) because
v1 REAL rows were captured on the v1 battery and must not be mixed.

---

## A3. Power / bound — so a second zero is a *quantified* finding, not a shrug

At the re-run's per-model support of **N = 120 suspicious cases** (case-level modal
decision over 2 seeds × 2 variants), a **clean 0-miss sweep** is not "no signal";
it is an **upper bound** on the true miss rate:

- **Rule of three:** 0 misses in N=120 ⇒ 95% upper bound ≈ 3/120 = **2.5%**.
- **Wilson 95% upper (0/120):** ≈ **3.1%**.
- Pooled across 4 models (case-level N up to 480) the bound tightens further
  (rule of three ≈ 3/480 ≈ **0.6%**).

The analysis will **report these bounds explicitly** (added to `claims.json` and
`PILOT_VERDICT.md`), so a second KILL reads as *"per-model realistic-hardness miss
rate is bounded at ≲X% (95%)"* rather than as an ambiguous null.

**Correlation-feasibility corollary (the deeper question this pilot surfaced).**
The study measures *correlation of misses*, which requires **misses to exist in
quantity**. If the hardened miss rate is, say, ~2–3%, then joint misses (all K
models missing the *same* case) are rarer still, and estimating the joint-miss
ratio with a usable CI would require an N far beyond what `BUDGET_FULL` can afford.
Therefore a hardened miss rate below the measurable band is not merely a null — it
is a **feasibility falsification** of the full study, obtained for ~\$1. This is a
legitimate and decision-relevant result.

---

## A4. Pre-committed outcome mapping (fixed now, before results exist)

Read the hardened re-run's `PILOT_VERDICT.md` and apply, without further
discretion:

1. **Pooled miss in the measurable band [10%, 70%] AND joint-miss estimable with
   signal (R>1, finite CI) AND within/cross contrast computable** →
   **PILOT: PASS.** The prereg **freezes on the hardened battery** and the full
   study proceeds per `PREREGISTRATION.md §8`. This amendment's battery becomes the
   study battery.

2. **Pooled miss < 10% (including the bounded ~2–3% case) OR joint-miss not
   estimable** → **PILOT: KILL (feasibility).** The standing contingency fires:
   **T4-A "From Flips to Dollars" swaps in as P4** — near-zero new data collection,
   reuses P3's dataset, comfortably inside the **Aug 15** trigger and the
   **mid-Sept** submission date on the **Oct 20** path. AML monoculture goes to the
   drawer with its kill-shot status updated. The bounded negative result becomes an
   **optional post-filing short note** ("frontier models exhibit near-zero miss
   rates on realistically-serialized FATF typologies, bounded at ≤X% at 95%") —
   honest and real, but **not load-bearing** for the primary timeline.

3. **Pooled miss > 70%** → **PILOT: KILL (degenerate)** — models miss almost
   everything; a different problem (task mis-specification), not the paper's thesis.
   Same contingency as (2).

No outcome triggers a *further* battery change. There is exactly one hardening
pass (this one); after the re-run we take criterion (1)/(2)/(3) as they fall.

---

## A5. Dual-use restatement (binding)

Hardening = **realism** derived from FATF/SAML-D, applied once, model-blind. It is
**not** a search for cases that beat a screener; no arm inspects model outputs to
choose case content; difficulty remains a design attribute, not a tuned target.
The frozen prereg §7 continues to bind in full.

---

*Amendment 1 ends. The battery generator is modified to satisfy H1–H4, the battery
is regenerated and re-frozen (new SHA-256), and the re-run is executed once under
A2 with the outcome handled per A4.*
