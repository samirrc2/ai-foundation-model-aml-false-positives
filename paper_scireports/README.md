# Scientific Reports submission package

**Manuscript:** *The choice of foundation model determines the false-positive burden of large language model anti-money-laundering transaction screening*
**Authors:** Samir Chincholikar (first author); Robin Chawla (corresponding author)
**Target:** *Scientific Reports* (Springer Nature), Article.

This folder contains everything needed to submit, plus the reproducibility trail.

## What to upload at submission

| Submission item | File here |
|---|---|
| Manuscript (single file; Word preferred, PDF/LaTeX accepted) | `MANUSCRIPT_ScientificReports_compiled.pdf` (from `latex/main.tex`) or convert `MANUSCRIPT_ScientificReports.md` to Word |
| Individual figure files (vector) | `figures/fig1_fp_by_model.pdf` … `figures/fig4_typology_miss.pdf` |
| Supplementary Information (single PDF) | `SUPPLEMENTARY_INFORMATION.md` → export to PDF |
| Cover letter | `COVER_LETTER.md` |

## Contents

```
paper_scireports/
├── MANUSCRIPT_ScientificReports_compiled.pdf   compiled Springer Nature LaTeX (12 pp) — the submission PDF
├── MANUSCRIPT_ScientificReports.md             Markdown source (for Word conversion / reference)
├── COVER_LETTER.md                             cover letter (corresponding author: Robin Chawla)
├── SUPPLEMENTARY_INFORMATION.md                Supplementary Notes + Tables S1–S4
├── CHECKLIST_Scientific_Reports.md             compliance table against the SR guidelines
├── AUDIT.md                                    file-by-file audit against SR standards
├── stats_tests.json                            machine-readable statistical test outputs
├── figures/                                    fig1–4 as vector PDF (+ PNG preview)
└── latex/                                       LaTeX source: main.tex, sn-jnl.cls, figures, README
```

## Format compliance (summary)

Title 16/20 words (scientific, no idiom); abstract 198/200 words, unstructured, no
references; main text ≈ 2,400/4,500 words; structure Introduction → Results (with
subheadings) → Discussion (no subheadings) → Methods; 4 figures + 2 tables (≤ 8);
mandatory Data-availability, Author-contributions, Competing-interests and Ethics
statements present; Nature statistical reporting (Cochran's Q, McNemar exact with
Bonferroni, Wilson intervals, cluster bootstrap; exact P-values; α and tails
stated); numbered references. Full item-by-item status in `CHECKLIST_Scientific_Reports.md`
and `AUDIT.md`.

## Reproducibility

Every reported number is reproduced byte-identically by the companion Code Ocean
capsule (`../codeocean/`), which regenerates and hash-verifies the data and recomputes
all statistics. Insert its DOI in the manuscript's Data-availability statement on
acceptance.

## Author to-do before submission (cannot be automated)

1. Add the three suggested-reviewer names/emails in `COVER_LETTER.md`.
2. Insert the public repository / Code Ocean DOI in the Data-availability statement.
3. Export `SUPPLEMENTARY_INFORMATION.md` to a single PDF.
4. Confirm affiliations (currently "Independent Researcher") and the corresponding-author contact.
5. If submitting Word: convert `MANUSCRIPT_ScientificReports.md` to `.docx` (equations editable).
