# Same Transactions, Different Alarms

### Foundation-model choice as an ungoverned driver of false-positive burden in LLM anti-money-laundering screening

On an identical, preregistered battery of 600 FATF/SAML-D-anchored cases (300 legitimate
hard-negatives, 300 suspicious across eight typologies), five foundation LLMs are run as
zero-shot AML screeners. On the **same** legitimate transactions, per-model false-positive
rates span **0.3% → 83.0%** (an 82.7-point spread), the models disagree on **85.7%** of
legitimate cases, and the operating point projects to a **~197× swing** in daily alert
volume at realistic prevalence. The variance is not a task limit — it is inherited from an
unexamined, silently-mutable model-selection decision. Framed as a model-risk-governance
problem (SR 11-7 / OCC 2011-12; NIST AI RMF; EU AI Act).

> Target venue: **Discover Artificial Intelligence** (Springer Nature). A prior draft
> targeted *Scientific Reports* (see `paper_scireports/`). The original P4 thesis
> (correlated *misses* / monoculture) was preregistered, tested, and falsified; this paper
> is its honest, stronger inversion — divergence in *false alarms*. See `PIVOT_KILLSHOTS.md`
> and `PREREGISTRATION_PIVOT.md`.

All results are a deterministic function of the frozen capture: **no re-runs, $0, no API
keys** are needed to reproduce any number below.

---

## Headline numbers (frozen capture, config `13ddae93dec88ed8`, 12,120 rows)

| Model | Provider | False-positive rate | Miss rate | Precision | Recall | Specificity | F1 | MCC |
|---|---|---|---|---|---|---|---|---|
| Gemini Flash | Google | 0.3% | 12.0% | 99.6% | 88.0% | 99.7% | 93.5% | 0.883 |
| GPT-4o | OpenAI | 1.0% | 3.3% | 99.0% | 96.7% | 99.0% | 97.8% | 0.957 |
| GPT-4.1-mini | OpenAI | 23.7% | 3.7% | 80.3% | 96.3% | 76.3% | 87.6% | 0.742 |
| Gemini Flash-Lite | Google | 24.7% | 0.7% | 80.1% | 99.3% | 75.3% | 88.7% | 0.769 |
| GPT-4o-mini | OpenAI | 83.0% | 0.0% | 54.6% | 100.0% | 17.0% | 70.7% | 0.305 |

Overall difference in false-positive rate: Cochran's Q = 131.6, df = 4, P ≈ 2×10⁻²⁷.
Pairwise separation by McNemar exact (Bonferroni). All rates carry Wilson 95% CIs; spreads
and per-typology rates carry cluster-bootstrap 95% CIs (2,000 draws, seed 4242).

---

## Layout

```
MANUSCRIPT.md              legacy JMLC draft (superseded; retains outdated "non-monotone" framing)
PREREGISTRATION.md         frozen day-1 contract (original monoculture P4)
PREREGISTRATION_PIVOT.md   frozen contract for this paper (false-positive divergence)
PREREGISTRATION_AMENDMENT.md  external-standard battery hardening (H1–H4)
PIVOT_KILLSHOTS.md         why the paper pivoted; the measured signals
DECISIONS.md               append-only log of every judgment call (D1–D19)
ARCHITECTURE.md            the CAPTURE↔ANALYSIS wall; the "screening cell" atom
RUNBOOK.md                 exact local commands (dry-run → probe → capture → analysis)
claims.json / pivot_claims.json   machine-readable results with CIs + config hash

config/     schema.py, models.yaml, battery.yaml, grid.yaml, loader.py
capture/    secrets, probe, build_battery, agent(+mock), ledger, orchestrator, freeze
data/       battery/ (frozen, hashed) · raw/ (frozen capture CSVs) · frozen/ (receipts)
analysis/   miss, stats, altrisk, baselines, alertvolume, figures_stats,
            stats_extended  →  classification metrics + paired tests + figures
pilot/      verdict.py → PILOT_*.md   (v1_KILL/ preserves the killed pilot — do not remove)

paper_discover/     CURRENT submission package (Discover AI): MANUSCRIPT_Discover.md,
                    references_discover.bib (56 refs), classification_metrics.*, figures/
paper_scireports/   prior Scientific Reports package (LaTeX, figures, cover letter)
codeocean/          one-command reproducibility capsule (own git; reproduce.sh)
submission/         packaged submission artifacts (own git)
```

## Reproduce every number ($0, offline, no API keys)

```bash
# From the frozen capture, recompute the extended analysis (metrics + paired tests + figures):
cd analysis && OUTDIR=../paper_discover python3 stats_extended.py

# Or the full reproducibility capsule (data-integrity check + byte-identical replication):
cd codeocean && bash reproduce.sh
```

`analysis/stats_extended.py` standardises the modal-vote tie rule on **ties → flag**
(preregistered, DECISIONS D4) across **both tables and figures**, resolving an earlier
inconsistency where `figures_stats.py` broke ties toward *miss* (which over-reported miss
rates in the figures relative to the tables).

## Method in one screen

The atom is a **screening cell** = (model, prompt_variant, seed, case). Each model screens
every battery case and returns constrained JSON `{suspicious, typology, rationale}`. A
**false positive** = a benign case flagged; a **miss** = a suspicious case not flagged.
Replicates reduce to a per-(model, case) **modal** decision (ties → flag). Inference:
Cochran's Q + McNemar exact (Bonferroni) on the paired FP decisions, Wilson intervals on
every proportion, and a cluster bootstrap over the eight typology strata.

## Dual-use discipline

We **measure** over-flagging of legitimate activity and cross-model disagreement — a
supervisory / model-risk concern. No arm searches for, ranks, or reports screener-beating
laundering text. The battery is synthetic and typology-anchored (FATF / SAML-D / AMLSim),
not an evasion catalogue. Framing is supervisory throughout.

## Data & reproducibility

Battery generator, frozen capture, analysis code, both preregistrations and the amendment,
and the machine-readable claims accompany the paper. Capture cost was ~US$8; all analysis is
deterministic and reproduces at zero cost. A one-command Code Ocean capsule
(`codeocean/`) verifies data integrity and confirms byte-identical outputs across runs.
