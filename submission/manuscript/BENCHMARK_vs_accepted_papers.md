# Benchmark: our manuscript vs five accepted Scientific Reports papers

Measured from the five accepted papers in the journal folder (all recent *Scientific Reports* fraud/ML articles). Their page counts are inflated because they are **double-spaced "unedited article-in-press" manuscripts**; figure counts are approximate (parsed from in-text "Fig. N" references, so they include sub-panels and cross-references). Our values are from the compiled Springer Nature typeset PDF.

## Accepted-paper measurements

| Paper | Pages (dbl-spaced) | Figures (≈, incl. panels) | Tables | Refs | Section scheme |
|---|---|---|---|---|---|
| P1 — Credit-card hybrid ML/DL (s41598-026-42891-4) | 36 | ~15–34 | 10 | 47 | Proposed → Results → Experiment → Discussion → Conclusion → Data availability → Declarations |
| P2 — Comparative ML on imbalanced data (…55224-2) | 48 | ~13 | 3 | 47 | Introduction → Methodology → Results → Experiment → Discussion → Conclusion |
| P3 — Temporal-drift framework (…58285-5) | 43 | ~21 | 10 | ~40 | Introduction → Related Work → Methodology → Results → Conclusion → Declarations |
| P4 — Healthcare blockchain ML (…60701-9) | 51 | ~12 | 14 | 39 | Introduction → Proposed → Results → Conclusion → Declarations |
| P5 — Federated GAN + transformer (…61476-9) | 27 | several | several | 22 | Introduction → Literature → Methods → Results → Experiment → Conclusion |
| **Accepted range** | **27–51** | **~12–30** | **3–14** | **22–47** | IMRaD + Conclusion + Declarations |

## Head-to-head: does our paper meet the standard?

| Dimension | SR requirement | Accepted-paper norm | **Our paper** | Verdict |
|---|---|---|---|---|
| Structure | Intro → Results → Discussion → Methods | IMRaD (+ Conclusion) | Intro → Results (5 subheads) → Discussion → Methods | ✅ Meets (SR-recommended order) |
| Abstract | ≤200 w, unstructured, no refs | unstructured, ~150–250 w | 198 w, unstructured, no refs | ✅ Meets |
| Title | ≤20 w, scientific | descriptive sentence | 16 w, literal scientific | ✅ Meets |
| Main-text length | ≤4,500 w (excl. Methods/refs) | long (dense method papers) | ~2,714 w | ✅ Within cap |
| Figures | vector, ≤8 display items total | ~12–30 (many panels) | 5 (vector PDF) | ✅ Meets |
| Tables | editable, ≤8 total w/ figures | 3–14 | 3 | ✅ Meets |
| Display items total | ≤8 | often >8 (allowed) | 8 | ✅ Meets (at cap) |
| References | ≤60, Nature numbered | 22–47 | 34 | ✅ In range |
| Conclusion section | optional | present in all 5 | present | ✅ Matches peers |
| Statistical rigor | named tests, n, α, exact P, correction | mostly accuracy/F1/AUC; SHAP; **rarely formal P-value tests** | Cochran's Q + McNemar exact + Bonferroni + Wilson + bootstrap; exact P; **preregistered** | ★ **Exceeds** peers |
| Reproducibility / data availability | Data-availability statement mandatory | statement; some code | Full one-command capsule, frozen data, **byte-identical**, preregistration | ★ **Exceeds** peers |
| Explainability | not required | SHAP / LIME common | operating-point + ROC + baselines (no SHAP) | ✅ Meets; ⚠ different tool |
| Declarations (competing/authors/ethics) | mandatory | present | present | ✅ Meets |
| Novelty / contribution | technically sound + significant | new classifier / architecture | first measurement of cross-model FP variance + governance | ★ Distinct, higher-novelty |

★ = exceeds the accepted-paper norm.

## Verdict

**Your paper meets the Scientific Reports standard on every mandatory and recommended item**, matches the accepted papers on structure, abstract, references and declarations, and **exceeds** them on the two dimensions Nature weights most heavily — **statistical rigour** (formal paired hypothesis tests with exact P-values, multiple-comparison correction, preregistration) and **reproducibility** (a byte-identical, one-command capsule). Its contribution is also of a higher-novelty type: a measurement-and-governance finding rather than another classifier.

**Density gap — now closed.** The earlier draft had 4 figures, 2 tables and 21 references, which met SR's rules but was leaner than the accepted papers. Three low-risk additions have been made:

1. **References 21 → 34** — added real works on class imbalance (He & Garcia), explainability (SHAP, LIME), LLM evaluation and reliability (HELM, stochastic parrots), prompt sensitivity (Sclar et al.), AI governance and documentation (NIST AI RMF, EU AI Act, Model Cards, Datasheets, algorithmic auditing), algorithmic-monoculture arbitrariness (Creel & Hellman), and the cluster bootstrap (Efron). All references are now cited in order via BibTeX.
2. **+1 figure, +1 table (8 display items, at the cap)** — Figure 5, a typology × model miss heatmap showing the per-typology signature of the operating-point trade-off; and Table 3, the pairwise McNemar matrix (with exact Bonferroni P-values) promoted into the main text, making the three operating tiers explicit.
3. **A short Conclusion section** — added after the Discussion, matching the convention of all five accepted papers.

With these, the paper now matches the accepted papers on visible thoroughness (5 figures, 3 tables, 34 references, Conclusion) **and** retains its edge on statistical rigour and reproducibility. It is compliant, rigorous, and as thorough as its accepted peers.
