# The choice of foundation model determines the false-positive burden of large language model anti-money-laundering transaction screening

*Prepared for Scientific Reports (Article).*

> **Note.** This Markdown is a reference / Word-conversion draft. The **authoritative, current manuscript** is the compiled Springer Nature LaTeX (`latex/main.tex` → `MANUSCRIPT_ScientificReports_compiled.pdf`), which carries **34 references** (BibTeX, `latex/sn-bibliography.bib`), **5 figures + 3 tables**, and a **Conclusion**. Figures are in `figures/`. Where this file and the LaTeX differ, the LaTeX governs.

**Samir Chincholikar**¹ and **Robin Chawla**¹*

¹ Independent Researcher.
*Corresponding author: Robin Chawla (robin.chawla.cse14@iitbhu.ac.in). Co-author: samir.chincholikar@gmail.com.
ORCID: S.C. 0009-0007-2779-3492; R.C. 0009-0007-2807-3948.

---

## Abstract

Large language models are being adopted to screen financial transactions for money laundering, but the consequences of choosing one foundation model over another have not been measured. We evaluated five widely used foundation models as zero-shot anti-money-laundering screeners on an identical, preregistered set of 600 synthetic cases anchored to recognised laundering typologies, half of them legitimate transactions designed to resemble alerts. On the same legitimate transactions, the rate at which models raised a false alarm ranged from 0.3% to 83.0%, a difference of 83 percentage points, and the models disagreed on 86% of legitimate cases. The variation was systematic: within each provider the false-alarm rate fell monotonically as model capability rose, so the smallest, cheapest models over-flagged (83.0%) while their flagship siblings did not (1.0%). Each model therefore occupies a different point on the trade-off between catching laundering and over-flagging legitimate activity, and because institutions commonly substitute a cheaper model to cut cost, that choice moves a deployment toward a high-false-positive regime. Projected to realistic conditions, this choice changes the daily alert workload about two hundred–fold. Because the model behind a commercial interface can change without notice, this operating point is an unmanaged risk that current oversight does not capture.

**Keywords:** anti-money laundering; large language models; false positives; model risk; transaction monitoring; foundation models

---

## Introduction

Money laundering is estimated to move 2–5% of global gross domestic product each year, and financial institutions are legally obliged to monitor transactions and report suspicious activity [1]. The dominant technology for this task, rules-based transaction monitoring, is widely criticised for generating enormous volumes of false alarms — commonly cited as exceeding 90% of all alerts — which impose heavy analyst review costs and drive the "de-risking" of legitimate customers [2,3]. This false-positive burden, rather than raw detection accuracy, is the central operational problem in anti-money-laundering (AML) compliance.

Large language models (LLMs) — general-purpose foundation models trained on broad data and adapted to many tasks with natural-language instructions [4,5] — are now being proposed and piloted as flexible AML screeners that can read heterogeneous transaction context and reason about laundering typologies without task-specific training. Existing evaluations of LLMs and of machine-learning methods for financial-crime detection focus on a capability question: how accurately can a model detect fraud or laundering [6–9]. This framing implicitly treats "an LLM" as a single, interchangeable component.

Two features of that literature are worth making explicit, because our results speak to both. First, the defining statistical challenge in financial-crime detection is extreme class imbalance: genuinely suspicious activity is rare, so much work concentrates on resampling and cost-sensitive learning — most prominently the synthetic minority over-sampling technique and its hybrids — and on comparing many classical, ensemble and deep models to minimise the false-positive rate at a fixed recall [14]. Recent studies extend this toolkit with generative and federated architectures and with post-hoc explainability (SHAP, LIME) to make alerts auditable, and with drift-aware frameworks that monitor a deployed model for degradation as transaction patterns evolve. Second, and central to our argument, all of this work assumes the model, once selected, is a fixed artefact whose behaviour changes only through retraining or measurable drift. A bespoke in-house classifier satisfies that assumption; a foundation model accessed through a commercial interface does not — its weights are controlled by the provider, are opaque to the institution, and can be replaced, re-priced or retired without notice and without any retraining event a drift monitor would observe. The false-positive problem the fraud-detection literature seeks to reduce through better models and resampling is, we show, also created — across two orders of magnitude — simply by which foundation model is placed behind the screener, before any tuning; and explainability tools that make a single alert auditable are silent on the counterfactual that a different, equally defensible model would have raised a different alert at a different rate.

We therefore ask a different and, we argue, more consequential question for governance: holding the screening task fixed, how much does the choice of foundation model change the outcome? Institutions accessing LLMs through commercial application programming interfaces (APIs) select among several providers and model versions, and providers routinely update, re-price, and retire those versions. If two otherwise-identical deployments screening the same activity with two different models produce materially different false-alarm rates, then a decision that is currently treated as procurement — which model to call — silently determines a core risk parameter.

We show that this is the case, and that the effect is large. Using a preregistered, fully reproducible design, we ran five foundation models as zero-shot screeners over an identical battery of 600 synthetic cases anchored to the Financial Action Task Force (FATF) typology catalogue and to established synthetic-AML data structures [10,11]. On identical legitimate transactions, per-model false-positive rates spanned two orders of magnitude; within each provider the rate fell monotonically as model capability rose, so cheaper, smaller models over-flagged far more; and each model implied a different operating point on the sensitivity–specificity trade-off. We quantify the operational consequence for alert volume, locate the models against rules-based and supervised baselines, and argue that the operating point of an LLM screener — and its instability under model substitution — must be brought inside model-risk governance.

## Results

### Foundation models diverge by 83 percentage points in false-positive rate on identical transactions

Each of five models (GPT-4o-mini, GPT-4.1-mini, GPT-4o from OpenAI; Gemini Flash and Gemini Flash-Lite from Google) screened all 600 cases under two prompt phrasings and two random seeds, returning a structured suspicious/not-suspicious decision (Methods). A false positive is a legitimate ("benign") case flagged as suspicious; a miss is a suspicious case not flagged. Per-case decisions were the majority vote over the four replicates.

On the 300 legitimate cases, false-positive rates ranged from 0.3% (Gemini Flash; 1 of 300) to 83.0% (GPT-4o-mini; 249 of 300) — a spread of 82.7 percentage points (95% confidence interval [CI] 69.2–95.3, cluster bootstrap over typology strata) (Fig. 1, Table 1). The five models differed in false-positive rate far beyond chance (Cochran's Q = 131.6, degrees of freedom = 4, P ≈ 2 × 10⁻²⁷; the five models are related raters scored on the same cases). The models fell into three statistically distinct tiers: pairwise McNemar exact tests (Bonferroni-corrected across the ten model pairs, two-tailed) separated the two cautious models (Gemini Flash, GPT-4o) from the two intermediate models (GPT-4.1-mini, Gemini Flash-Lite) from GPT-4o-mini, with every between-tier comparison at P < 10⁻¹⁹, while the two comparisons within a tier were not distinguishable (P = 1.0). Across models, the flag decision was not unanimous on 85.7% of legitimate cases (95% CI 75.1–95.4).

### False-positive rate falls monotonically with model capability within each provider

The variation is not idiosyncratic but highly systematic: within each provider, the false-positive rate decreases monotonically as model capability (and price) increases (Fig. 2, Table 1). In the OpenAI family, the smallest model GPT-4o-mini flagged 83.0% of legitimate cases, the intermediate GPT-4.1-mini 23.7%, and the flagship GPT-4o only 1.0%; in the Google family, the smaller Gemini Flash-Lite flagged 24.7% and the more capable Gemini Flash only 0.3%. In both families, without exception, the cheaper, smaller model is the more over-flagging one.

This monotonic dependence does not weaken the governance concern — it sharpens it. Because a model's price tracks its capability, the most common cost optimisation in production LLM deployments — routing traffic from a flagship model to a smaller, cheaper variant — moves a deployment predictably and steeply toward a high-false-positive operating point, and providers can perform such substitutions silently. The risk is therefore not that model choice has unpredictable effects, but that the default choice under cost pressure (the cheapest model) is systematically the worst on false positives, while the trade-off is undisclosed and ungoverned. Capability does not, however, rescue LLM screening: the flagships' low false-positive rates are bought at a recall cost (Gemini Flash missed 12.0% of suspicious cases), the cheap models' near-perfect recall is bought at catastrophic false-positive rates, and a tuned classifier and even a rules baseline dominate the cheaper models (Fig. 2). The cross-model dispersion is concentrated at the low-capability tier: the two smallest models differ by 58 percentage points (24.7% vs 83.0%), whereas the two flagships converge near zero (0.3% vs 1.0%) — so provider choice matters most precisely where cost pressure pushes institutions.

Plotting each model by its false-positive rate and its sensitivity (the fraction of suspicious cases caught) shows that the models are scattered across the operating curve (Fig. 2): GPT-4o-mini sits at maximum sensitivity and minimum specificity (catches everything, flags 83% of legitimate activity), whereas Gemini Flash is highly specific but misses 12.0% of suspicious cases. The choice of model therefore selects an entire operating point — a miss-prone regime or an alert-flooding regime — not merely a level of "accuracy".

### The operating point translates into a ~200-fold difference in alert workload

Screening performance on a balanced battery measures discrimination; operational burden depends on the low real-world prevalence of suspicious activity and is dominated by false positives. Projecting each operating point to a representative institution processing 1,000,000 transactions per day at a suspicious prevalence of 0.1% (Fig. 3, Table 2), the daily alert queue ranges from about 4,200 alerts (Gemini Flash) to about 830,000 (GPT-4o-mini) — a roughly 197-fold difference on identical activity — while the fraction of alerts that are genuinely suspicious (precision) collapses from 20.9% to 0.12%. At the GPT-4o-mini operating point, approximately 999 of every 1,000 alerts are false.

### Locating the models against non-LLM baselines

To provide a reference frame we evaluated two non-LLM screeners on the identical 600 cases (Methods). A deterministic rules baseline encoding FATF red-flag heuristics produced a 12.0% false-positive rate with an 11.3% miss rate, and a supervised classifier (gradient boosting on engineered features, evaluated out-of-fold) achieved near-zero false positives and misses. The task is therefore not intrinsically difficult: a tuned classifier separates the classes almost perfectly, and even a simple rules system reaches a 12% false-positive rate. Against this frame (Fig. 2, Table 2), the LLMs are dispersed across — and frequently worse than — the incumbent baselines: GPT-4o-mini's false-positive rate is roughly seven times that of the rules baseline, whereas GPT-4o and Gemini Flash are competitive with a tuned classifier on false positives. The dispersion is thus a property of using untuned foundation models, whose operating points are inherited rather than chosen.

### A shared trade-based blind spot, prompt sensitivity that preserves the ordering, and no correlated misses

Where the models do miss, they miss together on specific typologies (Fig. 4). Pooled across models, trade-based laundering was missed 18.9% of the time (95% CI 14.0–25.1) and cash-intensive fronts 10.3%, whereas structuring, layering, mule networks, funnel accounts, shell layering and rapid pass-through were caught almost perfectly (miss rates ≤ 1.6%). Trade-based laundering, which turns on economic-substance judgements not visible in transaction structure, is thus the typology where human escalation remains necessary regardless of model choice. Prompt phrasing shifted each model's operating point in a consistent direction — the FATF-typology prompt was uniformly the more aggressive, raising every model's false-positive rate (Gemini Flash 0.3%→2.3%, GPT-4o 0.3%→7.7%, GPT-4.1-mini 20.7%→36.7%, Gemini Flash-Lite 24.7%→44.0%, GPT-4o-mini 78.7%→85.0%). This within-model shift (2–19 percentage points; overall decision-flip rate 7.5%, 95% CI 6.9–8.2) was small relative to the between-model divergence and preserved the tier ordering, so the divergence is a property of the models, not an artefact of a particular prompt. As a preregistered secondary analysis we tested the competing algorithmic-monoculture prediction that shared foundation models would fail on the *same* cases; we found the opposite: no suspicious case was missed by all five models, per-model miss rates were low (0.0–12.0%), and chance-corrected agreement on the miss label was near zero (mean pairwise Cohen's κ = 0.072; range −0.011 to 0.26). The robust cross-model effect is divergence in false alarms, not homogenisation of misses.

## Discussion

Our central finding is that, on identical transactions, the choice of foundation model swings the AML false-alarm rate across two orders of magnitude, that this variation falls monotonically with model capability within each provider so that cheaper, smaller models over-flag far more, and that it translates into a roughly two-hundred-fold difference in analyst workload at realistic prevalence. The operating point that governs an institution's suspicious-activity workload, its rate of de-risking legitimate customers, and its residual exposure to missed laundering is therefore set by a model-selection decision that is currently treated as procurement rather than as a governed risk parameter. This is not the claim that institutions will knowingly deploy a screener that false-alarms on 83% of legitimate activity; a competent validation would detect that immediately. It is the claim that the operating point is undisclosed by providers, that it tracks the model's capability and hence its price — so that cost-driven substitution moves it predictably toward more false alarms — and that it can move without any action by the institution. A provider that upgrades a model, re-routes traffic from a flagship to a cheaper variant to reduce cost, or retires a version can move a deployment from one column of Table 1 to another — potentially a hundred-fold change in alert burden — with no model-inventory event and no revalidation trigger. We encountered this instability directly: during data collection a provider deprecated the model snapshots we had selected, forcing a substitution to a differently behaving model. Supervisory guidance on model risk management already requires that vendor and third-party models be inventoried, validated and monitored under consistent principles [3]; our results identify a specific, measurable and currently ungoverned risk channel within that mandate — the operating point implied by model selection and its drift under substitution. Three practices follow: treat the model snapshot, not merely "the provider's API", as the inventoried model so that a substitution is a governance event; require disclosure or measurement of the false-positive and miss operating point on a standard battery before and after any model change; and back-test heterogeneously, because a single accuracy number conceals the operating-point divergence documented here. The alert-volume projection (Table 2) offers a template for expressing the operating point in the currency that supervisors and operations teams use — expected alert queue and precision at the institution's own prevalence. Our results also speak to a broader concern that shared foundation models could homogenise decisions and correlate failures across institutions; we preregistered and tested a correlated-miss hypothesis and found the opposite for false alarms — sharp, idiosyncratic divergence rather than homogenisation — which calls for disclosure and operating-point control rather than enforced heterogeneity (see Methods and Supplementary Information for the reported null). Several limitations bound these conclusions. The battery is synthetic by necessity rather than convenience: real transaction records carrying ground-truth laundering labels cannot be shared, because suspicious-activity determinations are confidential by statute and customer transactions are protected by financial-privacy and data-protection law, so typology-anchored synthetic batteries (SAML-D, AMLSim) are the standard evaluation substrate in this field. Consequently, although anchored to FATF typologies and built with hard negatives, absolute rates will differ on production data, and we measure discrimination on a balanced set and project to operational prevalence rather than measuring against real alert dispositions. A second limitation concerns model identification: two of the five models (the Gemini pair) were reachable only through undated "-latest" aliases (Methods), so their exact snapshot cannot be pinned in the way the OpenAI models can — a provider-imposed constraint that both weakens reproducibility for those two models and directly illustrates the disclosure gap this paper argues must be closed. The study covers five models from two providers, a snapshot of mid-2026, and does not include reasoning or open-weight models, so the monotone capability–false-positive relationship, although consistent across both families here, should be confirmed on additional providers, reasoning models and open-weight models. The supervised baseline is an optimistic ceiling on synthetic structure, and we evaluate zero-shot screeners, whereas a production deployment would tune and threshold — the governance gap we identify concerns precisely the substitution of the underlying model beneath such a deployment. Within these bounds, the finding is robust across two prompt phrasings, two seeds, three chance-corrected agreement statistics and cluster-bootstrap resampling, and it is reproducible end-to-end from frozen data. The practical message for institutions and supervisors is that foundation-model selection in AML screening is a first-class model-risk decision: the model behind the interface, and any change to it, must be inventoried, its operating point disclosed and monitored, and human escalation preserved for economic-substance typologies such as trade-based laundering whichever model is chosen.

## Conclusion

We measured, on identical transactions, how much the choice of foundation model changes the outcome of LLM anti-money-laundering screening, and found that it changes it enormously: false-positive rates on legitimate activity ranged from 0.3% to 83% across five widely used models, this variation fell monotonically with model capability within each provider so that cheaper, smaller models over-flagged far more, and it projects to a roughly two-hundred-fold difference in analyst alert workload at realistic prevalence. Model choice thus silently selects an entire operating point on the sensitivity–specificity trade-off, and because the model behind a commercial interface can be upgraded, downgraded or retired without notice, that operating point is an unmanaged and drifting model risk rather than a fixed, validated property. Foundation-model selection and substitution in AML screening should therefore be treated as first-class model-risk events — the specific snapshot inventoried, its false-positive and miss operating point disclosed, measured on a standard battery and monitored on every version change, and human escalation preserved for economic-substance typologies. The preregistered design, frozen data and one-command reproducible capsule accompanying this work provide a template for such measurement.

## Methods

**Case battery.** We generated a deterministic, offline battery of 600 synthetic cases (seed 20260715) anchored to the FATF typology catalogue and to the structure of established synthetic-AML datasets (SAML-D; IBM AMLSim lineage) [10,11]. Each case is a small transaction sub-network serialised as a plain-text ledger of accounts (with know-your-customer and jurisdiction attributes) and transfers (amount, date, direction, channel). Half of the cases are suspicious, spanning eight typologies (structuring, layering, trade-based, mule networks, shell layering, funnel accounts, rapid pass-through, cash-intensive fronts); half are legitimate "hard negatives" — patterns such as payroll, treasury sweeps, documented trade finance and marketplace payouts, constructed to superficially resemble alerting conditions so that a model flagging every case cannot score well. To avoid leaking the label, cases contain raw transaction logs only (no natural-language summary), use irregular sub-threshold amounts rather than uniform values, interleave the typology signal with legitimate background transactions, and disperse transactions in time. The battery generator, the resulting file and its SHA-256 hash are provided; the reproduction pipeline regenerates the battery from the seed and verifies the hash.

**Models and screening procedure.** Five foundation models were accessed through their providers' APIs at temperature 0: GPT-4o-mini (gpt-4o-mini-2024-07-18), GPT-4.1-mini (gpt-4.1-mini-2025-04-14) and GPT-4o (gpt-4o-2024-11-20) from OpenAI, and Gemini Flash and Gemini Flash-Lite from Google, accessed via the provider's `gemini-flash-latest` and `gemini-flash-lite-latest` aliases, which at the capture date (July 2026) resolved to Gemini 3.5 Flash and Gemini 2.5 Flash-Lite respectively. Unlike OpenAI's dated snapshot identifiers, Google's public aliases did not expose an immutable dated version string — itself a concrete instance of the disclosure gap our results motivate (see Discussion). Each model screened every case under two supervisory prompt phrasings (a concise compliance-officer instruction and an FATF-typology-aware instruction) and two random seeds, yielding 5 × 2 × 2 × 600 = 12,000 screening calls. Models returned a constrained JSON object indicating whether the activity was suspicious; unparsable or failed calls were recorded as errors (overall error rate 0.08%) and excluded from the per-case majority vote. Provider models are updated and retired over time; one provider deprecated a selected snapshot during data collection, which is reported as an instance of the substitution effect analysed here.

**Estimands and statistics.** The primary quantities are the per-model false-positive rate on the 300 legitimate cases and the spread (maximum − minimum) across models; secondary quantities are cross-model disagreement on legitimate cases, per-typology miss rate, and prompt-variant decision change. Because the five models screen the same cases, they are related (paired) raters. We tested the overall difference in false-positive rate with Cochran's Q test for k related binary samples (k = 5, n = 300; degrees of freedom = k − 1 = 4), and pairwise differences with McNemar's exact (binomial) test on discordant cases, two-tailed, α = 0.05, Bonferroni-corrected across the ten model pairs. Proportions are reported with 95% Wilson score confidence intervals; the spread, divergence and per-typology rates additionally carry 95% percentile confidence intervals from a cluster bootstrap that resamples the eight typology strata (2,000 resamples, seed 4242). We use "significant" only when accompanied by a P value and otherwise use "substantial" or "large". Chance-corrected agreement across models was additionally summarised with Cohen's κ, Scott's π and Gwet's AC1 (Supplementary Information); the correlated-miss null is reported there.

**Baselines.** On the identical 600 cases we evaluated (i) a deterministic rules baseline encoding FATF red-flag heuristics (sub-threshold structuring, mule fan-in, shell-entity wires, high-risk-jurisdiction wires, rapid pass-through) and (ii) a supervised baseline (logistic regression and gradient-boosting classifiers on engineered graph features — counts of cash transfers, sub-threshold amounts, fan-in, shell entities, high-risk jurisdictions, temporal span), evaluated with 5-fold stratified out-of-fold prediction. Because the synthetic battery's structure encodes the typologies, the supervised baseline is an optimistic ceiling and is reported as such.

**Operational projection.** For an institution processing N = 1,000,000 transactions per day at suspicious prevalence p = 0.001, expected daily alerts are FP·N·(1 − p) + (1 − miss)·N·p, false alerts FP·N·(1 − p), and precision the ratio of true to total alerts; we report these per model and per baseline (Table 2).

**Software and reproducibility.** Analyses used Python 3.12 with NumPy 2.2.6, scikit-learn 1.7.2, SciPy 1.15 and Matplotlib 3.10; data collection additionally used the OpenAI and Google Python SDKs. Figures were produced with Matplotlib. All analysis is deterministic and reproduces byte-identically from the frozen data. The complete code, frozen data, preregistration and a one-command reproducible capsule are available (Data availability). No large language model is listed as an author; LLMs are the object of study, and any use of an LLM in drafting was limited to language editing under author verification, consistent with the journal's authorship policy.

**Ethics.** This study used only synthetic data and did not involve human participants, human tissue or animals; no ethical approval was required.

## Data availability

The synthetic battery generator, the frozen 12,000-call dataset, the analysis code, the frozen preregistration, and a one-command reproducible capsule (which regenerates and hash-verifies the battery, recomputes every reported statistic, and confirms byte-identical outputs across runs) are openly available in a public repository and Code Ocean capsule [persistent DOI to be inserted on acceptance]. All numbers reported here, with their confidence intervals and the configuration hash that produced them, are included as a machine-readable file in that repository.

## Author contributions

S.C. conceived the study, designed and preregistered the analysis, implemented the data-collection and analysis software, performed the experiments and analysis, and produced the figures. R.C. contributed to the study design, the interpretation of results, and the critical revision of the manuscript. Both authors wrote, reviewed and approved the final manuscript. ORCID: S.C. 0009-0007-2779-3492; R.C. 0009-0007-2807-3948.

## Competing interests

The authors declare no competing interests.

## Acknowledgements

Analyses used open-source software (Python, NumPy, scikit-learn, SciPy, Matplotlib). The author thanks the maintainers of these projects.

## Figure legends

**Figure 1. False-positive rate of five foundation models on identical legitimate transactions.** Bars show the percentage of 300 legitimate cases each model flagged as suspicious; error bars are 95% Wilson score confidence intervals. Rates span 0.3–83.0% (Cochran's Q = 131.6, degrees of freedom = 4, P ≈ 2 × 10⁻²⁷).

**Figure 2. Each model occupies a different operating point.** Sensitivity (percentage of 300 suspicious cases caught) versus false-positive rate (percentage of 300 legitimate cases flagged) for the five foundation models (circles) and the two non-LLM baselines (triangles: rules heuristic; supervised classifier). Within a provider, the more capable model is not consistently the more conservative.

**Figure 3. Projected daily alert workload at realistic prevalence.** Expected daily alerts for each screener at a suspicious prevalence of 0.1% over 1,000,000 transactions per day (logarithmic axis). Model choice changes the queue from about 4,200 to about 830,000 alerts on identical activity.

**Figure 4. A shared blind spot for trade-based laundering.** Miss rate by laundering typology, pooled across the five models; error bars are 95% Wilson score confidence intervals. Trade-based laundering and cash-intensive fronts are missed substantially more often than structural typologies.

**Figure 5. Miss rate by laundering typology and model.** Percentage of suspicious cases of each typology (rows) missed by each model (columns); darker cells indicate more misses. The cautious models (Gemini Flash, GPT-4o) concentrate their misses in trade-based laundering and cash-intensive fronts, while the alert-flooding GPT-4o-mini misses almost nothing — the per-typology signature of the operating-point trade-off.

## Tables

**Table 1. Per-model operating point on the identical 600-case battery.** Values are percentages with 95% Wilson score confidence intervals; n = 300 legitimate and 300 suspicious cases.

| Model | Provider | False-positive rate | Miss rate |
|---|---|---|---|
| Gemini Flash | Google | 0.3 [0.1–1.9] | 12.0 [8.8–16.2] |
| GPT-4o | OpenAI | 1.0 [0.3–2.9] | 3.3 [1.8–6.0] |
| GPT-4.1-mini | OpenAI | 23.7 [19.2–28.8] | 3.7 [2.1–6.4] |
| Gemini Flash-Lite | Google | 24.7 [20.1–29.8] | 0.7 [0.2–2.4] |
| GPT-4o-mini | OpenAI | 83.0 [78.3–86.8] | 0.0 [0.0–1.3] |

**Table 2. Projected daily operational impact at 0.1% prevalence (1,000,000 transactions/day).** Rules and supervised baselines shown for reference; the supervised baseline is an optimistic ceiling on synthetic structure.

| Screener | False-positive rate (%) | Projected daily alerts (95% CI) | Alert precision (%) |
|---|---|---|---|
| Supervised (ceiling) | 0.0 | ~1,000 | 100 |
| Gemini Flash | 0.3 | 4,200 (1,500–19,500) | 20.9 |
| GPT-4o | 1.0 | 11,000 (4,400–29,900) | 8.8 |
| Rules baseline | 12.0 | 121,000 (88,700–162,000) | 0.7 |
| GPT-4.1-mini | 23.7 | 237,000 (193,000–289,000) | 0.4 |
| Gemini Flash-Lite | 24.7 | 247,000 (202,000–299,000) | 0.4 |
| GPT-4o-mini | 83.0 | 830,000 (784,000–868,000) | 0.1 |

*(95% intervals propagate the false-positive Wilson interval through the projection; counts rounded to three significant figures.)*

**Table 3. Pairwise comparison of false-positive rates (McNemar's exact test).** Same 300 legitimate cases for all models; b and c are discordant counts. P-values two-tailed, Bonferroni-corrected across the ten model pairs. The two within-tier pairs (top) are indistinguishable; every between-tier pair is separated at P < 10⁻¹⁸.

| Model pair | b | c | P (Bonferroni) |
|---|---|---|---|
| Gemini Flash vs GPT-4o | 1 | 3 | 1.0 |
| GPT-4.1-mini vs Gemini Flash-Lite | 42 | 45 | 1.0 |
| Gemini Flash vs GPT-4.1-mini | 1 | 71 | 3.1×10⁻¹⁹ |
| Gemini Flash vs Gemini Flash-Lite | 1 | 74 | 4.0×10⁻²⁰ |
| GPT-4o vs GPT-4.1-mini | 0 | 68 | 6.8×10⁻²⁰ |
| GPT-4o vs Gemini Flash-Lite | 0 | 71 | 8.5×10⁻²¹ |
| GPT-4.1-mini vs GPT-4o-mini | 1 | 179 | 2.4×10⁻⁵¹ |
| Gemini Flash-Lite vs GPT-4o-mini | 8 | 183 | 2.5×10⁻⁴³ |
| Gemini Flash vs GPT-4o-mini | 0 | 248 | 4.4×10⁻⁷⁴ |
| GPT-4o vs GPT-4o-mini | 0 | 246 | 1.8×10⁻⁷³ |

## References

*(Nature numbered style; author to verify each entry and apply exact Springer Nature formatting at submission.)*

1. Financial Action Task Force. *Trade-Based Money Laundering: Trends and Developments* (FATF, 2020).
2. United Nations Office on Drugs and Crime. *Money Laundering and Globalization* (UNODC, 2011).
3. Board of Governors of the Federal Reserve System & Office of the Comptroller of the Currency. Supervisory guidance on model risk management (SR 11-7 / OCC Bulletin 2011-12) (2011).
4. Brown, T. et al. Language models are few-shot learners. *Adv. Neural Inf. Process. Syst.* **33**, 1877–1901 (2020).
5. Bommasani, R. et al. On the opportunities and risks of foundation models. Preprint at https://arxiv.org/abs/2108.07258 (2021).
6. Gamal, N., Younis, E. M. G. & Makram, W. M. Enhancing credit card fraud detection with a hybrid approach using machine and deep learning. *Sci. Rep.* (2026). https://doi.org/10.1038/s41598-026-42891-4
7. Shi, X., Zhang, Y., Yu, M. & Chen, J. Advanced fraud detection in financial systems: a comparative study of machine learning models on imbalanced data. *Sci. Rep.* (2026). https://doi.org/10.1038/s41598-026-55224-2
8. Zuberi, N. et al. A robust machine learning framework for detecting temporal drift in financial fraud prevention. *Sci. Rep.* (2026). https://doi.org/10.1038/s41598-026-58285-5
9. Juyal, P. K., Kolluri, J. & Siripuri, K. Federated generative adversarial network with hybrid transformer-GRU and explainable AI for financial fraud detection. *Sci. Rep.* (2026). https://doi.org/10.1038/s41598-026-61476-9
10. Oztas, B. et al. Enhancing anti-money laundering through a synthetic transaction monitoring dataset (SAML-D). In *Proc. IEEE Int. Conf. e-Business Engineering* (2023).
11. Weber, M. et al. Anti-money laundering in bitcoin: experimenting with graph convolutional networks for financial forensics. Preprint at https://arxiv.org/abs/1908.02591 (2019).
12. Kleinberg, J. & Raghavan, M. Algorithmic monoculture and social welfare. *Proc. Natl Acad. Sci. USA* **118**, e2018340118 (2021).
13. Bommasani, R., Creel, K. A., Wang, D., Li, J. & Liang, P. Picking on the same person: does algorithmic monoculture lead to outcome homogenization? *Adv. Neural Inf. Process. Syst.* **35** (2022).
14. Chawla, N. V., Bowyer, K. W., Hall, L. O. & Kegelmeyer, W. P. SMOTE: synthetic minority over-sampling technique. *J. Artif. Intell. Res.* **16**, 321–357 (2002).
15. Pedregosa, F. et al. Scikit-learn: machine learning in Python. *J. Mach. Learn. Res.* **12**, 2825–2830 (2011).
16. Wilson, E. B. Probable inference, the law of succession, and statistical inference. *J. Am. Stat. Assoc.* **22**, 209–212 (1927).
17. Cochran, W. G. The comparison of percentages in matched samples. *Biometrika* **37**, 256–266 (1950).
18. McNemar, Q. Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika* **12**, 153–157 (1947).
19. Gwet, K. L. Computing inter-rater reliability and its variance in the presence of high agreement. *Br. J. Math. Stat. Psychol.* **61**, 29–48 (2008).
20. OpenAI. GPT-4 technical report. Preprint at https://arxiv.org/abs/2303.08774 (2023).
21. Gemini Team, Google. Gemini: a family of highly capable multimodal models. Preprint at https://arxiv.org/abs/2312.11805 (2023).
