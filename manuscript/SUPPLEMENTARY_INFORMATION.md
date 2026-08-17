# Supplementary Information

**Same Transactions, Different Alarms: Foundation-Model Choice and AML False Positives**

Samir Chincholikar, Robin Chawla

*Submitted as a single PDF (Discover Artificial Intelligence requirement). Numbering is separate from the main article; items are Supplementary Table S1–S3, Supplementary Note, and Supplementary Methods.*

---

## Supplementary Note: preregistration and design

The study estimands, battery specification, screening-cell definition, and analysis were fixed in a frozen preregistration prior to the confirmatory analysis (provided in the reproducibility repository as `preregistration_pivot.md`, with the original monoculture preregistration and its amendment). The battery was generated deterministically (seed 20260715) and SHA-256-hashed; the reproducibility capsule regenerates it from the seed and verifies the hash. The confirmatory analysis was run on a fresh capture over the expanded five-model set; the earlier pilot is reported in the preregistration as exploratory/hypothesis-generating.

All analysis is deterministic and reproduces byte-identically from the frozen 12,000-call dataset (2 prompt variants × 2 seeds × 600 cases × 5 models). Overall error rate (unparsable/failed calls) was 0.08%. The full pairwise McNemar comparison of per-model false-positive rates is reported in the main article (Table 2).

---

## Supplementary Table S1. Battery composition (600 cases)

| Class | n | Categories |
|---|---|---|
| Suspicious | 300 | structuring, layering, trade-based, mule networks, shell layering, funnel accounts, rapid pass-through, cash-intensive fronts (≈38 each) |
| Legitimate (hard negatives) | 300 | payroll fan-out, treasury sweeps, genuine trade finance, retail settlement, marketplace payouts, loan disbursement, remittance corridor, subscription billing (≈38 each) |

Difficulty spread ≈ 30% easy / 40% medium / 30% hard within each class. Cases are raw node/edge transaction ledgers with no natural-language label, irregular sub-threshold amounts, typology signal interleaved with legitimate background volume, and realistic temporal dispersion.

---

## Supplementary Table S2. Per-typology miss rate (pooled across five models)

95% Wilson score confidence intervals; n as indicated.

| Typology | Miss rate | 95% CI | n (model×case) |
|---|---|---|---|
| Trade-based | 18.9% | 14.0–25.1 | 190 |
| Cash-intensive front | 10.3% | 6.7–15.5 | 185 |
| Rapid pass-through | 1.6% | 0.6–4.7 | 185 |
| Structuring | 0.5% | 0.1–2.9 | 190 |
| Funnel account | 0.0% | 0.0–2.0 | 185 |
| Layering | 0.0% | 0.0–2.0 | 190 |
| Mule network | 0.0% | 0.0–2.0 | 190 |
| Shell layering | 0.0% | 0.0–2.0 | 185 |

---

## Supplementary Table S3. Correlated-miss null (preregistered secondary analysis)

Unlike the false-positive side, model misses were rare and did not co-occur: no suspicious case was missed by all five models, and cross-model agreement on the miss label (chance-corrected) was near zero.

| Quantity | Value |
|---|---|
| Per-model miss rate | 0.0%–12.0% (main text, Table 1) |
| Mean pairwise Cohen's κ on misses | 0.072 (range −0.011 to 0.26) |
| Joint miss by all five models | 0 of 300 suspicious cases |
| Independence-predicted joint miss | ≈0 |

Interpretation: the algorithmic-monoculture prediction of correlated failure is not supported for false alarms in this setting; the robust effect is divergence (in false positives), not homogenisation. Chance-corrected agreement was additionally summarised with Scott's π and Gwet's AC1, which agree with κ in sign and magnitude (near zero).

---

## Supplementary Methods: baselines

**Rules baseline.** Deterministic FATF red-flag heuristics: (i) ≥3 sub-threshold cash deposits converging on one beneficiary; (ii) fan-in ≥5 low-value senders; (iii) shell entities (no employees / newly incorporated) in a wire chain; (iv) high-risk-jurisdiction wires with limited KYC; (v) rapid same-day large pass-through. Result: false-positive 12.0%, miss 11.3%.

**Supervised baseline.** Logistic-regression and gradient-boosting classifiers on engineered features (counts of cash transfers, sub-threshold amounts, fan-in degree, shell entities, high-risk jurisdictions, limited-KYC nodes, temporal span, transfer counts), evaluated with 5-fold stratified out-of-fold prediction (scikit-learn 1.7.2, seed 4242). Result (gradient boosting): false-positive ≈0.0%, miss ≈0.0%. Because the synthetic battery's structure encodes the typologies, this is an optimistic ceiling and is reported as such.

---

## Data and code availability

All data, code, the preregistration, and a one-command reproducible capsule (regenerates + hash-verifies the battery, recomputes every statistic, and confirms byte-identical outputs across two runs) are available at https://github.com/samirrc2/same-transactions-different-alarms and in the Code Ocean capsule https://doi.org/10.24433/CO.4804007.v1. A machine-readable `pivot_claims.json` contains every reported number with its confidence interval and the configuration hash that produced it.
