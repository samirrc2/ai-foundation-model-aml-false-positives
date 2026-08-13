# PREREGISTRATION — P4′ "Same Transactions, Different Alarms"
### Foundation-model choice as an uncontrolled driver of AML false-positive burden

**Date:** 2026-07-16. **Kill-shot:** CLEAR & FEASIBLE (see the AML-pivot sweep,
2026-07-15/16). **Reuses:** the P4 capture apparatus, hardened FATF/SAML-D battery,
and CAPTURE↔ANALYSIS wall in full. **Supersedes** the AML-monoculture P4 (KILLED:
misses ≤6.6%, uncorrelated).

> **The integrity split — read this first.** The P4 real capture (3,840 decisions,
> config `45a398838805f39d`) was **inspected before these estimands were fixed**.
> It is therefore treated as an **EXPLORATORY, hypothesis-generating pilot** — its
> numbers are reported *as such*, never as confirmatory. This document pre-registers
> the **CONFIRMATORY** test: the same estimands, computed on a **fresh full-run
> capture over an expanded model set**, fixed here **before** that data is
> collected. Exploratory pilot values are quoted below only to justify powering the
> confirmatory run; they carry no confirmatory weight.

---

## 1. Claim

The choice of foundation LLM is an **uncontrolled driver of AML false-positive
(false-alarm) burden**. On *identical* legitimate transactions, per-model
false-positive rates diverge by a large margin, so a bank's SAR/alert load — and
the customers it de-risks — is set by an ungoverned model-selection decision. This
is the **operational, divergence-side inversion** of the monoculture worry: the
danger is not homogeneity of misses (falsified in P4) but **heterogeneity of false
alarms**.

Supporting: (B) LLM screeners have **systematic FATF-typology blind spots** (trade-
based laundering); (C) decisions are **mildly prompt-fragile**.

---

## 2. Estimands (frozen, confirmatory)

Unit = a screening cell (model, prompt_variant, seed, case); per-(model,case)
decision = modal flag over replicates (ties→flag, as P4). Benign cases carry
ground-truth **legitimate**; a **false positive** = a benign case flagged
suspicious.

**A — primary (false-positive burden and its cross-model divergence).**
- `FP_m` = per-model false-positive rate over benign cases (Wilson 95% CI).
- **`FP_spread` = max_m FP_m − min_m FP_m** (percentage points) — the headline;
  cluster-bootstrap CI over benign strata. Test: CI excludes 0.
- `FP_ratio` = max/min (reported when min>0; undefined/`≥` bound when a model's FP
  ≈ 0, which the pilot exhibits).
- **`divergence`** = fraction of benign cases on which the models' modal flags are
  not unanimous; cluster-bootstrap CI.

**B — supporting (typology blind spots).** Per-FATF-typology miss rate over
suspicious cases (Wilson CI); pre-registered focus: **trade_based** and
**cash_intensive_front** vs the rest. Test: trade-based miss CI lies above the
pooled non-trade-based miss.

**C — supporting (prompt fragility).** Decision-flip rate between prompt variants
at matched (model, case, seed); Wilson CI. Reported as a robustness note, not a
headline.

Inference: cluster bootstrap resampling **strata** (benign patterns for A;
typologies for B), seeded (`ANALYSIS_SEED=4242`), 2000 draws, 95% percentile CI —
identical machinery to P4 (`analysis/stats.py`, `analysis/altrisk.py`).

---

## 3. Exploratory pilot values (P4 capture — hypothesis-generating ONLY)

*Quoted to power the confirmatory run; NOT confirmatory.* Per-model FP: gemini_flash
**0.0%** (CI 0–3.1), openai_41_mini 21.7% (15.2–29.9), gemini_flash_lite 24.2%
(17.4–32.6), openai_4o_mini **80.8%** (72.9–86.9). `FP_spread` = **80.8 pp**
(bootstrap CI **[63.3, 95.0]**). Benign `divergence` = **84.2%**. Trade-based miss
**20.0%** vs ≤3% for structuring/layering/mule/shell. Prompt flip **8.2%**. These
imply the confirmatory effect is very large; the full run is powered to detect a
`FP_spread` far smaller than observed.

---

## 4. Confirmatory full-run design (frozen)

- **Models:** the 4 pilot models **+** `openai_4o` — **5 models across 2 families**
  (OpenAI ×3 mini→flagship, Google ×2), so "model choice" spans a realistic range.
  (`gemini_pro` excluded — forced-thinking, cost/latency-unsuited, D17; `xai_grok`
  excluded — xAI account out of credits, D19. Both remain in the registry for an
  optional one-model top-up if a reviewer requests a third family. The FP-variance
  headline is already large within these 5 models: pilot spread 0%→80%.)
- **Battery:** the whole hardened battery (600 cases; ≥300 benign hard-negatives),
  same FATF/SAML-D provenance and H1–H4 hardening.
- **Prompt variants:** 2 (`v_terse`, `v_fatf`). **Seeds:** 2. (Robustness dims
  trimmed to hold cost; the headline rests on MODEL BREADTH, which is kept in full.
  7 models exceeds the published AML-LLM norm of 1–4; see DECISIONS D16.)
- **Budget:** `BUDGET_FULL = $25` (realistic ~$19), same priced ledger + hard-abort
  + freeze. Cost calibrated to the literature and to the program's ~$15 (Paper 2) norm.
- **Endpoints:** exactly §2, emitted by `analysis/altrisk.py` → `pivot_claims.json`.

**Gate for "the effect is real & reportable":** confirmatory `FP_spread` CI
excludes 0 **and** `divergence` CI excludes 0. (The pilot makes a failure here very
unlikely, but the confirmatory run is what the paper reports.)

---

## 5. Dual-use (binding)

The paper measures **over-flagging of legitimate activity** and cross-model
disagreement — a supervisory / model-risk-management concern. **No arm** searches
for transactions that evade a screener; the typology-gap section (B) is framed as
*"where human escalation is mandatory,"* never as an evasion ranking. Difficulty
remains a fixed design attribute (H1–H4). The P4 dual-use constraint carries over
in full.

---

## 6. What is reused vs new
- **Reused verbatim:** `config/`, `capture/` (probe, agent, ledger, orchestrator,
  freeze), the hardened battery + hash, `analysis/{miss,stats}.py`, the wall, the
  ledger cap machinery.
- **New:** `analysis/altrisk.py` (the A/B/C estimands) and this preregistration.
- **Framing:** B9/B11 — model-concentration & governance risk; regulatory hook =
  alert fatigue, SAR over-reporting, model risk management (SR 11-7 / OCC 2011-12),
  de-risking. Venue: *J. Money Laundering Control* (fast, topical) / *Finance
  Research Letters*.

---

## 7. Stop / integrity rules
- Confirmatory results come only from the **fresh full-run capture**; the pilot's
  exploratory numbers are never relabeled confirmatory.
- ERROR first-class (>2% ⇒ non-authoritative); append-only; freeze+hash on landing;
  analysis pure/$0/byte-identical.
- One analysis pipeline (`altrisk.py`); no estimand is added after seeing the
  confirmatory data.

*Frozen 2026-07-16. `pivot_claims.json` (exploratory, from the P4 pilot) accompanies
this file; the confirmatory `pivot_claims.json` is produced by the full run.*
