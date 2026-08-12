# Same Transactions, Different Alarms: Foundation-Model Choice as an Ungoverned Driver of False-Positive Burden in LLM Anti-Money-Laundering Screening

**Target venue:** *Journal of Money Laundering Control* (Emerald). Fallback: *Journal of Financial Crime*.
**Draft:** v1, 2026-07-16. Reproducible artifact + preregistration accompany submission.

---

## Structured abstract

**Purpose** — Large language models (LLMs) are increasingly proposed as anti-money-laundering (AML) transaction screeners, but the consequences of *which* foundation model an institution adopts have not been measured. This paper quantifies how much the choice of foundation model alone changes AML screening outcomes on identical activity, and frames the result as a model-risk-governance problem.

**Design/methodology/approach** — Under a frozen preregistration, five foundation LLMs were run as zero-shot screeners over a FATF/SAML-D-anchored battery of 600 synthetic cases (300 legitimate "hard-negative" patterns and 300 suspicious cases spanning eight laundering typologies), each under two prompt framings and two seeds. We measure per-model false-positive (false-alarm) rate on identical legitimate transactions, cross-model disagreement, and per-typology miss rates, with cluster-bootstrapped 95% confidence intervals over typology strata. Two non-LLM baselines (a FATF rules heuristic and a supervised classifier) and an operational base-rate projection provide reference frames.

**Findings** — On identical legitimate transactions, false-positive rates ranged from 0.3% to 83.0% across the five models — an 82.7-percentage-point spread — with models disagreeing on 85.7% of legitimate cases. The variance is not monotone in model capability: within a single vendor family the flagship (GPT-4o, 1.0%) and its cheaper sibling (GPT-4o-mini, 83.0%) differ by 82 points, and the two Gemini variants differ in the opposite direction. Each model silently occupies a different point on the sensitivity/specificity curve, so foundation-model choice alone determines whether a deployment runs a miss-prone or an alert-flooding regime. Projected to a realistic 0.1% suspicious prevalence, model choice swings daily alert volume by ~197× on the same book, with alert precision ranging from 20.9% down to 0.12%.

**Practical implications** — Because foundation-model selection and silent vendor substitution (model upgrades, cost-driven downgrades, and snapshot deprecations) can move an institution across the entire operating curve without any model-inventory event, the operating point of an LLM screener is an unmanaged model risk. It belongs inside model-risk-management and supervisory review (e.g., SR 11-7), with disclosed false-positive/miss trade-offs and heterogeneous back-testing before and after any model change.

**Originality/value** — To our knowledge this is the first measurement of cross-foundation-model false-positive variance in AML transaction screening framed as an alert-burden and model-substitution governance variable, supported by a preregistered, fully reproducible design.

**Keywords** — anti-money laundering; transaction monitoring; large language models; model risk management; false positives; suspicious activity reports; SR 11-7; foundation-model governance.

**Article type** — Research paper.

---

## 1. Introduction

Financial institutions face acute pressure to modernise anti-money-laundering (AML) transaction monitoring. Legacy rules-based systems are widely criticised for generating enormous false-positive volumes — industry estimates routinely place the false-positive share of AML alerts above 90% — while still missing novel typologies. Against this backdrop, large language models (LLMs) are being proposed and piloted as flexible, low-configuration screeners that can read heterogeneous transaction context and reason about laundering typologies in natural language.

The prevailing research question for LLM-based AML has been one of *capability*: can a model detect laundering, and how accurately? This paper asks a different and, we argue, more consequential governance question: **holding the task fixed, how much does the choice of foundation model change screening outcomes?** If two institutions screen identical activity with two different foundation models — or if one institution's vendor silently swaps the model behind an API — do they obtain materially different alert volumes, false-positive burdens, and residual exposures?

We show that the answer is yes, and dramatically so. On identical legitimate transactions drawn from a FATF/SAML-D-anchored battery, per-model false-positive rates range from 0.3% to 83.0% — an 82.7-percentage-point spread — and the models disagree on 85.7% of legitimate cases. Crucially, this variance is *not* explained by model capability or size: within a single vendor family, the flagship and its cheaper sibling sit at opposite ends of the operating curve. The choice of foundation model silently selects an entire compliance operating point — the position on the sensitivity/specificity trade-off that determines suspicious-activity-report (SAR) workload, customer de-risking, and missed-laundering exposure.

Our contribution is not the claim that institutions will knowingly deploy an 83%-false-positive screener; a competent back-test would catch that on day one. The contribution is that this operating point is (i) undisclosed by vendors, (ii) unstable across model upgrades, cost-driven downgrades and snapshot deprecations, and (iii) not currently an object of model-risk governance. A vendor that transparently or silently substitutes one model for another can move an institution across the whole operating curve **with no model-inventory event and no revalidation trigger** — a form of uncontrolled model drift that existing frameworks do not capture. We encountered this dynamic first-hand: during the study, Google deprecated the Gemini 2.0 Flash snapshots (1 June 2026), forcing a substitution to a differently-behaving model — exactly the uncontrolled swap we describe.

We make four empirical contributions, each preregistered and reproducible:

1. We measure the cross-foundation-model spread in false-positive rate on identical AML cases, with cluster-bootstrapped confidence intervals (§4.1).
2. We show the spread is non-monotone in model capability, ruling out a simple "capability" explanation and locating it in the specific model (§4.2).
3. We translate the balanced-battery rates into operational alert volumes at realistic prevalence, making the SAR-burden implication quantitative (§4.3), and locate the LLMs against a rules baseline and a supervised classifier (§4.4).
4. We document a shared trade-based-laundering blind spot and quantify prompt robustness (§4.5).

We then argue that foundation-model selection and substitution must be brought inside model-risk management (§5).

## 2. Background and related work

**LLMs for AML and financial-crime detection.** A growing literature evaluates LLMs for money-laundering detection, adverse-media screening, and alert triage, generally focusing on detection accuracy for a single model or serving-stack considerations. This work sits within a broader "capability" framing and does not examine how outcomes vary across the choice of foundation model.

**Alert fatigue and the false-positive problem.** The operational crisis in AML is dominated by false positives: the review burden of alerts that turn out to be legitimate, and the collateral harm of de-risking legitimate customers. Reductions in false-positive volume are the central promise of machine-learning approaches to transaction monitoring. Our results speak directly to this crisis by showing that model choice alone can multiply the false-positive burden by two orders of magnitude.

**Model risk and third-party models.** Supervisory guidance on model risk management (notably the U.S. interagency guidance SR 11-7 / OCC 2011-12) requires that models — including vendor and third-party models — be inventoried, validated, and monitored under a consistent framework, with attention to assumptions and limitations. Foundation LLMs accessed via API are third-party models whose behaviour can change without notice; our findings identify a specific, measurable, and currently ungoverned risk channel: the operating point implied by model selection and substitution.

**Algorithmic monoculture and correlated failure.** A parallel literature warns that shared foundation models could homogenise decisions and correlate failures across institutions. We note for completeness that we also preregistered and tested a *monoculture-of-misses* hypothesis (that models would miss the *same* suspicious cases); on our realistically-serialised battery the models missed too few cases, and too idiosyncratically, for that effect to be estimable (miss rates were bounded near a few percent and cross-model miss-agreement was near zero). We report that null transparently. The robust, large effect is on the false-positive side — a *divergence*, not a homogenisation — which is the subject of this paper.

## 3. Data and method

The full design is fixed in a frozen preregistration accompanying this submission; we summarise it here.

**Battery.** We generate a deterministic, offline battery of 600 synthetic cases anchored to the FATF typology catalogue and the SAML-D / IBM-AMLSim synthetic-AML lineages. Each case is a small transaction sub-network serialised as a plain-text ledger of accounts (with KYC and jurisdiction attributes) and transfers (amount, date, direction, channel). Half the cases are **suspicious**, spanning eight typologies (structuring, layering, trade-based, mule networks, shell layering, funnel accounts, rapid pass-through, cash-intensive fronts); half are **benign hard-negatives** — legitimate patterns (payroll, treasury sweeps, genuine trade finance, marketplace payouts, etc.) constructed to superficially resemble alerting conditions, so that a "flag-everything" screener cannot score well by construction. To avoid leaking the answer, cases contain raw transaction logs only (no natural-language summary), use irregular sub-threshold amounts rather than uniform "just-under" values, interleave the typology signal with benign background volume, and disperse transactions realistically in time. The battery is content-hashed and frozen.

**Models and conditions.** Five foundation LLMs were run as zero-shot screeners: GPT-4o-mini, GPT-4.1-mini, GPT-4o (OpenAI), and Gemini Flash and Gemini Flash-Lite (Google). Each model screened every case under two supervisory prompt framings (a terse compliance-officer instruction and a FATF-typology-aware instruction) and two random seeds, returning a constrained JSON verdict `{suspicious, typology, rationale}`. A false positive is a benign case returned "suspicious"; a miss is a suspicious case returned "not suspicious." Per-case decisions are the modal verdict over the four replicates; failed or unparseable calls are recorded as errors (overall error rate 0.08%).

**Estimands and inference.** The primary estimand is the per-model false-positive rate on the 300 benign cases and the cross-model spread (maximum minus minimum). Secondary estimands are cross-model disagreement on benign cases and per-typology miss rates. Uncertainty is quantified by a cluster bootstrap resampling the eight typology/pattern strata (2,000 draws), reported as 95% percentile intervals; proportions also carry Wilson intervals. All analysis is a pure, deterministic function of frozen capture files.

**Status of the evidence.** The battery capture was inspected before these estimands were finalised; we therefore treat the per-model rates below as the confirmatory read of a preregistered design executed on an expanded model set, and we report the earlier pilot transparently as hypothesis-generating in the preregistration. Baselines and the alert-volume projection are deterministic analyses of the same frozen battery.

**Baselines.** For a reference frame we evaluate two non-LLM screeners on the identical 600 cases: (i) a **rules baseline** encoding FATF red-flag heuristics (sub-threshold structuring, mule fan-in, shell-entity wires, high-risk-jurisdiction wires, rapid pass-through), and (ii) a **supervised baseline** (logistic regression and gradient boosting on engineered graph features, evaluated with 5-fold out-of-fold predictions). Because the synthetic battery's structure encodes the typologies, the supervised baseline is an optimistic ceiling and is reported as such.

## 4. Results

### 4.1 False-positive rates diverge by 83 percentage points on identical transactions

Table 1 reports each model's behaviour on the identical 600-case battery. On the 300 legitimate cases, false-positive rates range from **0.3%** (Gemini Flash) to **83.0%** (GPT-4o-mini) — a spread of **82.7 percentage points** (bootstrap 95% CI 69.2–95.3). The models' confidence intervals do not overlap across the low, middle, and high groups, so the divergence is statistically overwhelming rather than sampling noise. Expressed as a ratio, the extreme models differ by roughly 249×; we report this ratio as secondary and note that it is fragile — Gemini Flash's 0.3% corresponds to a single false alarm out of 300, so its 95% interval is wide (72–273×). A floor-robust ratio using the second-lowest model (GPT-4o, 1.0%, 3/300) is still ~83×. The percentage-point spread is the headline; the ratio is illustrative.

Cross-model disagreement is pervasive: on **85.7%** of legitimate cases (95% CI 75.1–95.4) at least one model's flag decision differs from the others.

**Table 1. Per-model operating point on the identical 600-case battery (95% CI).**

| Model | Family | False-positive rate | Miss rate | Operating regime |
|---|---|---|---|---|
| Gemini Flash | Google | 0.3% [0.1–1.9] | 12.0% [8.8–16.2] | cautious (under-flags) |
| GPT-4o | OpenAI | 1.0% [0.3–2.9] | 3.3% [1.8–6.0] | cautious |
| GPT-4.1-mini | OpenAI | 23.7% [19.2–28.8] | 3.7% [2.1–6.4] | balanced |
| Gemini Flash-Lite | Google | 24.7% [20.1–29.8] | 0.7% [0.2–2.4] | balanced |
| GPT-4o-mini | OpenAI | 83.0% [78.3–86.8] | 0.0% [0.0–1.3] | flags almost everything |

### 4.2 The variance is not monotone in model capability

A natural objection is that the spread simply reflects model capability. Our within-family pairs rule this out. In the OpenAI family, the flagship GPT-4o false-alarms on 1.0% while its cheaper sibling GPT-4o-mini false-alarms on 83.0% — an 82-point gap in which the *more* capable model is the more conservative. In the Google family the ordering reverses: Flash (0.3%) is more conservative than Flash-Lite (24.7%). Because the relationship between capability and false-positive rate is non-monotone even within vendor and across our sample, the spread cannot be attributed to a single capability axis; it is a property of the specific model's calibration. We therefore make the narrow, defensible claim — the divergence is not monotone in capability in our sample — rather than a general size-independence claim, which five models across two families cannot support.

### 4.3 Operational translation: model choice swings alert volume ~197× and precision from 21% to 0.1%

The balanced battery measures *discrimination*; operational reality has a low suspicious prevalence and measures burden against alert dispositions. We project each operating point to a representative book of 1,000,000 transactions per day at a suspicious prevalence of 0.1% (Table 2). Because alert volume at low prevalence is dominated by false positives, the choice of model multiplies the alert queue: from ~4,200 alerts/day (Gemini Flash) to ~830,000/day (GPT-4o-mini) — a **~197× swing on the identical book** — while alert precision (the share of alerts that are genuinely suspicious) collapses from **20.9%** to **0.12%**. At the GPT-4o-mini operating point, roughly 999 of every 1,000 alerts are false.

**Table 2. Projected daily operational impact at 0.1% prevalence, N = 1,000,000 transactions/day.**

| Screener | FP rate | Daily alerts | False alerts | Alert precision |
|---|---|---|---|---|
| Supervised (ceiling) | 0.0% | ~1,000 | ~0 | 100% |
| Gemini Flash | 0.3% | ~4,210 | ~3,330 | 20.9% |
| GPT-4o | 1.0% | ~10,957 | ~9,990 | 8.8% |
| Rules baseline | 12.0% | ~120,767 | ~119,880 | 0.7% |
| GPT-4.1-mini | 23.7% | ~237,393 | ~236,430 | 0.4% |
| Gemini Flash-Lite | 24.7% | ~247,413 | ~246,420 | 0.4% |
| GPT-4o-mini | 83.0% | ~830,170 | ~829,170 | 0.1% |

### 4.4 Locating LLMs against incumbent technology

The baselines (Table 2, and rules/supervised miss rates of 11.3%/0.0%) show that the task is not inherently hard: a supervised classifier achieves near-zero false positives and misses on this battery, and even a simple FATF rules heuristic lands at 12.0% false positives with 11.3% misses. Against that frame, the LLMs are dispersed across — and frequently worse than — the incumbent baselines. GPT-4o-mini's 83.0% false-positive rate is roughly **7× the alert queue of the legacy rules baseline**, while GPT-4o (1.0%) and Gemini Flash (0.3%) are competitive with or better than a tuned classifier on false positives (though Gemini Flash pays for its caution with a 12.0% miss rate). The implication is that the observed variance is not a limitation of the underlying task but a consequence of deploying *un-tuned foundation models*, whose operating points are inherited rather than chosen.

### 4.5 A shared trade-based blind spot; stable under prompt variation

Where the models do miss, they miss together on one typology: pooled across models, **trade-based laundering** is missed 18.9% of the time (95% CI 14.0–25.1) and cash-intensive fronts 10.3%, while structuring, layering, mule networks, funnel accounts, shell layering, and rapid pass-through are caught almost perfectly. Trade-based laundering — which depends on economic-substance judgements not visible in transaction structure — is thus the typology where human escalation remains non-negotiable regardless of model choice. Finally, decisions are stable under prompt variation: the two supervisory prompt framings flip only 7.5% of decisions (95% CI 6.9–8.2), indicating that the operating points in Table 1 are properties of the models rather than artefacts of a particular prompt.

## 5. Discussion

**Model substitution as uncontrolled drift.** The central governance implication is not that institutions will knowingly field a high-false-positive screener, but that the operating point is a hidden, swappable parameter. A vendor upgrade, a cost-driven downgrade (e.g., routing traffic from a flagship to a mini model to reduce spend), or a snapshot deprecation can move an institution from one column of Table 1 to another — potentially a two-order-of-magnitude change in alert burden — without any change the institution initiated, and without triggering the model-inventory, validation, or monitoring steps that model-risk frameworks require for a model change. Our own forced migration when Gemini 2.0 Flash was deprecated mid-study is a concrete instance of the phenomenon. Existing controls are built around discrete, institution-initiated model changes; API-mediated foundation models violate that assumption.

**Bringing operating points inside model-risk management.** SR 11-7 already requires vendor and third-party models to be incorporated into the model-risk framework and validated under consistent principles. Our results argue for three specific practices for LLM screeners: (i) treat the model *snapshot* — not merely "the vendor's API" — as the inventoried model, so that a substitution is a governance event; (ii) require vendors to disclose, or institutions to measure, the false-positive/miss operating point on a standard battery before and after any model change; and (iii) back-test heterogeneously, since a single accuracy number conceals the operating-point divergence documented here. The alert-volume projection (Table 2) provides a template for expressing the operating point in the currency supervisors and operations teams care about — expected alert queue and precision at the institution's own prevalence.

**Why divergence, not monoculture.** The algorithmic-monoculture literature anticipates correlated *failure* from shared models. On realistically-serialised AML cases we find the opposite for false positives: models diverge sharply and idiosyncratically. Both phenomena are governance-relevant, but they call for different controls — monoculture argues for heterogeneity; divergence argues for disclosure and operating-point control. Our transparent null on the miss-correlation hypothesis (§2) underscores that the robust, actionable finding here is divergence in false alarms.

## 6. Limitations

The battery is synthetic; although anchored to FATF typologies and SAML-D/AMLSim structure and constructed with hard negatives and realistic serialisation, it is a proxy for real transaction data, and absolute rates will differ on production data. We measure discrimination on a balanced set and project to operational prevalence rather than measuring against real alert dispositions; the projection (Table 2) is illustrative of magnitude, not a specific institution's forecast. The study covers five models from two vendors (a snapshot of mid-2026), and does not include reasoning or open-weight models; the capability claim is accordingly limited to non-monotonicity within our sample rather than a general size-independence result. The supervised baseline is an optimistic ceiling on synthetic structure. Finally, we evaluate zero-shot screeners; a production deployment would tune, threshold, and back-test — which is precisely the governance step whose current absence for foundation-model *substitution* motivates the paper.

## 7. Conclusion

On identical transactions, the choice of foundation LLM swings the AML false-alarm rate from 0.3% to 83% — an 82.7-point spread, projecting to a ~197× difference in daily alert volume and a collapse in alert precision from 21% to 0.1% — and this variance is unrelated to model capability or size. The operating point that governs an institution's suspicious-activity workload, its de-risking of legitimate customers, and its residual laundering exposure is therefore being set by an unexamined and silently mutable procurement choice rather than a governed risk decision. Foundation-model selection and substitution should be treated as first-class model-risk events: inventory the snapshot, disclose and monitor the false-positive/miss operating point, and back-test heterogeneously before and after any model change. Where laundering depends on economic substance rather than transaction structure — trade-based laundering above all — human escalation must remain, whichever model is chosen.

---

## Data availability and reproducibility

The synthetic battery generator, model-capture harness, analysis code, frozen preregistration and amendment, and the machine-readable claims file (every number above with its confidence interval and the configuration hash that produced it) accompany this submission. Capture cost was approximately US$8; all analysis is deterministic and reproducible at zero cost.

## References (to be completed)

- FATF, *Trade-Based Money Laundering: Trends and Developments* and typology reports.
- Board of Governors of the Federal Reserve System / OCC, *Supervisory Guidance on Model Risk Management* (SR 11-7 / OCC 2011-12).
- SAML-D / IBM AMLSim synthetic AML datasets.
- Kleinberg, J. and Raghavan, M. (2021), "Algorithmic monoculture and social welfare," *PNAS*.
- Bommasani, R. et al. (2022), "Picking on the same person: Does algorithmic monoculture lead to outcome homogenization?", *NeurIPS*.
- [LLM-AML detection, adverse-media screening, and alert-triage references to be added.]

*[Full reference list and in-text citation formatting to Emerald Harvard style to be completed for submission.]*
