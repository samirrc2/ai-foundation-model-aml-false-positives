# File-by-file audit — Scientific Reports submission package

Audited against the *Scientific Reports* submission guidelines. ✅ meets standard; ⚠ author action required (cannot be automated).

## Committed files

| File | Role | Standard check | Status |
|---|---|---|---|
| `MANUSCRIPT_ScientificReports_compiled.pdf` | The compiled submission manuscript (Springer Nature LaTeX) | Compiles with `pdflatex` (0 errors, no undefined refs); 16 pages; renders title page, unstructured abstract, keywords, line numbers, figures, tables, declarations, numbered references | ✅ |
| `latex/main.tex` | LaTeX source | `sn-jnl` class, `sn-basic` Numbered style, `lineno`. Contains: 1 abstract, 6 keywords, Introduction, Results (5 subheadings), Discussion (no subheadings), Conclusion, Methods, Data-availability (`\bmhead`), Competing interests, Author contributions, Ethics, ORCIDs, 5 `\includegraphics`, 3 tables, BibTeX bibliography (34 refs) | ✅ |
| `latex/sn-bibliography.bib` | BibTeX database | 34 entries; all cited in text | ✅ |
| `latex/sn-basic.bst` | Springer Nature Nature-style bibliography style | Applies numbered Nature reference formatting | ✅ |
| `latex/main.bbl` | Generated bibliography (committed so it renders without a BibTeX run) | 34 numbered references | ✅ |
| `latex/sn-jnl.cls` | Springer Nature class (bundled for standalone compile) | Official template class, unmodified | ✅ |
| `latex/fig1–5_*.pdf` | Figures used by `\includegraphics` | Vector PDF | ✅ |
| `latex/README.md` | Compile instructions | Documents 2-pass pdflatex, no BibTeX needed | ✅ |
| `MANUSCRIPT_ScientificReports.md` | Markdown source (for Word conversion / reference) | Content identical to LaTeX; use to produce a `.docx` if submitting Word | ✅ |
| `COVER_LETTER.md` | Cover letter | States why appropriate for SR, declarations, prior-editor-discussion (none); corresponding author = Robin Chawla; suggested-reviewer slots present | ⚠ (fill 3 reviewer names) |
| `SUPPLEMENTARY_INFORMATION.md` | Supplementary Notes + Tables S1–S4 | Separate numbering (S1–S4); preregistration note; pairwise McNemar table; per-typology table; correlated-miss null; baseline methods | ⚠ (export to single PDF) |
| `CHECKLIST_Scientific_Reports.md` | Guideline compliance table | Every SR requirement mapped to status | ✅ |
| `AUDIT.md` | This file | — | ✅ |
| `README.md` | Package guide | Upload map + author to-do | ✅ |
| `stats_tests.json` | Machine-readable test outputs | Cochran's Q, pairwise McNemar, per-model rates, per-typology | ✅ |
| `figures/fig1–4_*.pdf` | Publication figures (vector) | See figure checks below | ✅ |
| `figures/fig1–4_*.png` | 300-dpi previews | For quick viewing / Word insertion | ✅ |
| `.gitignore` | Excludes build artifacts | Covers logs/aux/out/preview PNGs/bst | ✅ |

## Hard-limit checks (verified programmatically)

| Requirement | Limit | Actual | Status |
|---|---|---|---|
| Title | ≤ 20 words, no idiom | 16 words, literal scientific sentence | ✅ |
| Abstract | ≤ 200 words, unstructured, no refs | 200 words, single paragraph, no citations | ✅ |
| Main text (Intro+Results+Discussion+Conclusion) | ≤ 4,500 words | 3,099 words | ✅ |
| Keywords | ≤ 6 | 6 | ✅ |
| Display items | ≤ 8 | 5 figures + 3 tables = 8 | ✅ (at cap) |
| References | ≤ 60 | 34 (BibTeX, auto-numbered) | ✅ |

## Figure checks (Nature figure guidelines)

| Figure | Content | Vector? | Axis integrity | Error bars |
|---|---|---|---|---|
| Fig 1 | Per-model false-positive rate | PDF | y-axis 0–100% (not truncated) | 95% Wilson CI, defined in legend |
| Fig 2 | Operating points (sensitivity vs FP) | PDF | scatter (histogram-truncation rule N/A) | points; legend explains |
| Fig 3 | Projected daily alerts | PDF | log axis for a 1,000→830,000 range (honest, labeled) | N/A (deterministic projection) |
| Fig 4 | Per-typology miss rate | PDF | bars from 0 (not truncated) | 95% Wilson CI, defined in legend |
| Fig 5 | Typology × model miss heatmap | PDF | colour scale 0–100% | deterministic rates; legend explains |

All figures: sans-serif lettering, white background, thousands comma-separated, software/versions stated in Methods.

## Statistics checks (Nature statistical guidelines)

- Named tests: Cochran's Q (k related binary samples), McNemar exact (paired), Wilson score interval, cluster bootstrap — all named in Methods. ✅
- n stated (300 benign / 300 suspicious; 12,000 calls). ✅
- Test justified by the paired design (same cases, 5 models). ✅
- α = 0.05, two-tailed, **exact P-values** reported (Cochran Q P ≈ 2×10⁻²⁷; pairwise P-values in Supplementary Table S2). ✅
- Multiple comparisons: Bonferroni across 10 pairs. ✅
- "significant" used only with a P-value; CI-based claims phrased "substantial/large". ✅
- Table/figure legends state the 95% CI method. ✅

## Consistency checks

- Reported per-model false-positive rates in Table 1 (0.3 / 1.0 / 23.7 / 24.7 / 83.0%) match `stats_tests.json`. ✅
- Author order/roles consistent across manuscript, cover letter, SI, README: Samir Chincholikar (first), Robin Chawla (corresponding). ✅
- Every number in the manuscript is reproduced by the companion Code Ocean capsule (`../codeocean/`). ✅

## Not committed (git-ignored build artifacts)

`latex/main.pdf`, `latex/*.aux|*.log|*.out`, `latex/*-01.png`, `latex/pg-*.png`, `latex/bst/` — regenerable by `pdflatex`; excluded via `.gitignore`. (They remain on disk because this filesystem blocks deletion; remove locally before a raw archive if desired. The manuscript compiles without `bst/`.)

## Author to-do before submission (⚠)

1. Cover letter: add three suggested reviewers.
2. Data-availability: insert the public repository / Code Ocean DOI.
3. Export Supplementary Information to a single PDF.
4. Confirm affiliations and corresponding-author contact in the submission system.
5. Optional: convert the Markdown manuscript to Word if submitting `.docx`.

## Reviewer-feedback revisions applied

- **Capability framing corrected (critical).** An earlier draft claimed the false-positive variation was "not explained by capability" and "non-monotone," misreading the Google pair as a reversal. In fact both families are perfectly monotone: within each provider the false-positive rate falls as capability/size rises (OpenAI: GPT-4o 1.0% < GPT-4.1-mini 23.7% < GPT-4o-mini 83.0%; Google: Gemini Flash 0.3% < Gemini Flash-Lite 24.7%). The paper now states this directly and turns it into a sharper governance point — cost-driven substitution toward cheaper models predictably worsens the false-positive operating point — rather than a false capability-independence claim. Abstract, §Results, Discussion, Conclusion and cover letter all corrected.


- **Model identification.** The two Gemini models are now identified by the alias used *and* the model they resolved to at the capture date (Gemini 3.5 Flash; Gemini 2.5 Flash-Lite, July 2026), and the undated-alias issue is stated as both a reproducibility limitation and a concrete instance of the disclosure gap the paper argues must be closed — removing the internal tension with the "inventory the snapshot" recommendation.
- **Synthetic data reframed as domain-forced.** Limitations now explain that real labelled laundering data cannot be shared (SAR confidentiality; financial-privacy law), so typology-anchored synthetic batteries are the field-standard substrate — not a shortcut.
- **Table 2 carries uncertainty.** Projected daily-alert counts now show 95% intervals (propagated from the false-positive Wilson interval) and are rounded to three significant figures, replacing the spurious six-figure precision.
- **Prompt effect reported per model.** Per-model false-positive rate under each prompt (e.g. Gemini Flash-Lite 24.7%→44.0%) replaces the single pooled 7.5% flip; the FATF prompt is uniformly more aggressive but preserves the tier ordering.
- **Monoculture null promoted to the main text.** The preregistered negative now reports its numbers in Results (no case missed by all five models; mean pairwise miss κ = 0.072), not only in the Supplement.

**Verdict: the package meets the Scientific Reports required standard for a first submission; the remaining items are author-supplied inputs the journal requires (reviewers, DOI, affiliation confirmation).**
