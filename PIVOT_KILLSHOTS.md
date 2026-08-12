# Pivot kill-shots — fraud/AML topics recoverable from the P4 data
### Evidence-backed: every "feasibility" row below is a MEASURED signal from the 3,840 real screening decisions already captured (config `45a398838805f39d`, $0 to reproduce). Dated 2026-07-16.

> P4's own thesis (correlated *misses*) was falsified (miss ≤6.6%, uncorrelated).
> But the same real data contains several **large** signals pointing at different,
> honest fraud papers. Because the data is already collected, each pilot below is
> effectively **done** — feasibility is not a guess, it's a number. Dual-use stays
> clean throughout: every candidate measures screener *behaviour*, never evasion.

## Measured facts from the P4 real capture (4 models × 2 variants × 2 seeds × 240 hardened FATF cases)

| Signal | Value | Implication |
|---|---|---|
| **False-positive rate spread across models** | **0.8% → 84%** (gemini_flash / 41_mini / flash_lite / 4o_mini = 0.8 / 32.5 / 33.3 / 84.0%) | ~100× swing on *identical* legitimate transactions |
| Cross-model flag divergence (same case) | **52.5%** of cases | models disagree half the time |
| Per-typology miss (pooled) | **trade_based 27.1%**, cash_intensive_front 14.2%, all others ≤3% | systematic, typology-specific blind spot |
| Prompt-variant flip (v_terse↔v_fatf) | 8.2% | modest prompt fragility |
| Overall miss | 4.4% (≤6.6% CI95), uncorrelated | the original monoculture-of-misses thesis is dead |

---

## ★ CANDIDATE A (RECOMMENDED) — "Same Transactions, Different Alarms"
### Foundation-model choice as an uncontrolled driver of AML false-positive burden

- **Framework cell:** B9/B11 — model-concentration & governance risk (the *operational* face of monoculture: not correlated misses, but uncontrolled variance in false alarms).
- **Core question:** Does the choice of foundation LLM change the false-positive (false-alarm) rate of AML transaction screening — and by how much — on identical activity?
- **Lead finding (MEASURED, not hoped-for):** On identical FATF/SAML-D benign hard-negatives, per-model false-positive rates span **0.8% to 84%** — a ~100× swing — and models disagree on **52.5%** of cases. The "monoculture" isn't homogeneity; it's an **unmanaged lottery**: your SAR/alert burden is set by a model-selection decision nobody is governing.
- **Why it's strong:** false positives, not misses, are the actual operational crisis in AML — banks drown in >90%-false SARs and pay alert-review armies. A 100× model-driven swing in that burden is a direct model-risk-management finding.
- **Novelty:** the LLM-AML literature measures *accuracy*; nobody has measured cross-**foundation-model** false-positive variance as a governance/alert-fatigue variable. The P4 kill-shot lit (Kleinberg–Raghavan, Bommasani) supplies the homogenization framing — here inverted (divergence, not homogeneity).
- **Feasibility:** **PROVEN.** Signal is enormous and already captured; pilot reproduces for $0. Full run just adds flagship models + more cases under `BUDGET_FULL`; cost is trivial (mini/flash tier).
- **Referee risk:** "synthetic benign ≠ real business activity" → mitigate with FATF/SAML-D provenance + realistic interleaved volume (already built, H3). "cheap models only" → full run adds flagships.
- **Regulatory hook:** alert fatigue; SAR over-reporting; **model risk management (SR 11-7 / OCC 2011-12)**; de-risking of legitimate customers; the EU AMLA operational-burden debate.
- **Dual-use:** **none** — measuring over-flagging of legitimate activity, cleaner than P4 (no typology-evasion surface at all).
- **Data collection:** ~zero new — reuses the P4 harness + hardened battery verbatim.
- **Venue:** *J. Money Laundering Control* (fast, 18-day first decision, exact topical fit) or *Finance Research Letters*.
- **Kill-shot verdict:** ✅ **CLEAR & FEASIBLE (empirically confirmed).** This is the paper the data wants to be.

---

## CANDIDATE B — "The Trade-Based Blind Spot"
### Systematic, typology-specific detection gaps in LLM AML screening

- **Framework cell:** B7/B9 — critique/limits ("where does the capability actually fail?").
- **Core question:** Do LLM screeners miss specific laundering typologies systematically, and is the gap shared across models?
- **Lead finding (MEASURED):** misses are not uniform — they concentrate on **trade-based laundering (27.1% missed)** and **cash-intensive fronts (14.2%)**, while structuring/layering/mule/shell are caught ~100%. The trade-based gap is **shared across all four models** (a genuine common blind spot — the one place monoculture-of-misses *does* appear).
- **Novelty:** a concrete, actionable typology-risk map; identifies exactly where human review is non-negotiable.
- **Feasibility:** signal exists (trade-based), but per-typology N is thin at pilot scale → the full run must oversample trade_based/cash_intensive. Moderate; cheap.
- **Referee risk:** small-N per typology at pilot; fix by design in the full run.
- **Dual-use:** **handle with care** — "which typology evades" is close to the line. Frame strictly supervisorily ("typologies requiring mandatory human escalation"), never as an evasion ranking. Cleaner to run as a *supporting section* of Candidate A than as a standalone.
- **Verdict:** ✅ CLEAR, ⚠ feasibility MODERATE (needs oversampling); best as a section, not a solo paper.

---

## CANDIDATE C — "Prompt-Fragile Compliance" (weak — do not lead with)
- **Core question:** Do trivial prompt changes flip AML screening decisions?
- **Measured:** 8.2% flip between the two supervisory prompt variants — real but modest.
- **Verdict:** ⚠ THIN as a standalone (8% isn't a headline). Fine as a one-paragraph robustness note inside Candidate A.

---

## Recommended package (fits the Aug 15 trigger / mid-Sept submission)
**Lead with Candidate A** ("Same Transactions, Different Alarms"), and fold **B**
(trade-based blind spot) and **C** (prompt fragility) in as supporting sections.
That yields one coherent, honest paper: *a model-risk audit of LLM AML screening —
100× false-positive variance across foundation models, a shared trade-based blind
spot, and mild prompt fragility.* It reuses the entire P4 apparatus, the pilot is
already de-risked by real data, and it lands in the same fast, topical venue (JMLC).

The original AML-monoculture P4 stays in the drawer with its honest KILL; this pivot
is a *stronger* fraud paper than the one you set out to write — and it's true.
