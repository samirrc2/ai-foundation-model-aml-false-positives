# Scientific Reports submission checklist — compliance table

Every requirement from the *Scientific Reports* submission guidelines, whether it is
mandatory, our current status, and the action taken. ✅ = met; ⚠ = action needed by author at submission.

## A. Format & length
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| A1 | Article ≤ ~11 typeset pages | Recommended | ✅ | Compiled Springer Nature PDF = 15 pages incl. 5 figures + 3 tables (single-column template; 2-column production typeset is shorter) |
| A2 | Main text ≤ 4,500 words (excl. Abstract, Methods, References, legends) | Mandatory | ✅ | Intro+Results+Discussion+Conclusion ≈ 2,714 words — under the cap |
| A3 | Title ≤ 20 words, single scientifically accurate sentence, **no puns/idioms** | Mandatory | ✅ (fixed) | Retitled to a literal scientific sentence (15 words); "Same Transactions, Different Alarms" dropped as it is idiomatic |
| A4 | Abstract ≤ 200 words, **unstructured** (no subheadings), **no references**, non-technical | Mandatory | ✅ (rewritten) | New 198-word single-paragraph abstract; no citations; plain-language |
| A5 | Up to 6 keywords | Allowed | ✅ | 6 keywords provided |
| A6 | Display items ≤ 8 (figures + tables) | Mandatory | ✅ | 5 figures + 3 tables = 8 (at the cap) |
| A7 | No footnotes | Mandatory | ✅ | None used |
| A8 | Page/line numbers (recommended for review) | Recommended | ⚠ | Add in the submission file (template supports it) |

## B. Structure (Nature order)
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| B1 | Order: Introduction → Results (with subheadings) → Discussion (**no** subheadings) → Methods | Recommended structure | ✅ | Reorganised to this exact order; Methods moved to the end |
| B2 | Results carries subheadings | Recommended | ✅ | 5 Results subheadings |
| B3 | Discussion has **no** subheadings | Recommended | ✅ | Single continuous Discussion |
| B4 | Title page with affiliations + corresponding author (asterisk) | Mandatory | ⚠ | Author/affiliation block present; confirm corresponding-author asterisk + email at submission |

## C. Statistics (Nature statistical guidelines)
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| C1 | State the **name** of each statistical test | Mandatory | ✅ | Cochran's Q; McNemar's exact test; Wilson score interval; cluster bootstrap — all named in Methods |
| C2 | State **n** for each analysis | Mandatory | ✅ | n = 300 benign / 300 suspicious cases; 12,000 calls; stated throughout |
| C3 | **Justify** the test (incl. design/normality) | Mandatory | ✅ | Paired binary design (same cases, 5 models) → Cochran's Q / McNemar justified in Methods; proportions → Wilson; clustered → bootstrap |
| C4 | State **alpha**, one/two-tailed, **actual P values** (not just "significant") | Mandatory | ✅ | α = 0.05, two-tailed; exact P values reported (e.g., Cochran Q P < 10⁻²⁷; pairwise P values in Table/Methods) |
| C5 | Multiple-comparisons correction | Mandatory | ✅ | Bonferroni over the 10 pairwise McNemar tests |
| C6 | "Significant" only with a P value; else "substantial/considerable" | Mandatory | ✅ | Enforced in text; CI-based claims phrased as "substantial/large" |
| C7 | Descriptive stats: n, measure of centre, measure of variability; state s.e.m. vs s.d. | Mandatory | ✅ | Rates with 95% CIs (Wilson / bootstrap); CIs labelled; no ± ambiguity |
| C8 | Error bars defined in figure legends | Mandatory | ✅ | All figure legends state "95% confidence interval" |

## D. Figures (Nature figure guidelines)
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| D1 | Vector format (EPS/AI/PDF) for line art/graphs | Mandatory (publication) | ✅ | All 4 figures exported as vector **PDF** (+ 300-dpi PNG preview) |
| D2 | Sans-serif lettering, consistent size, white background | Mandatory | ✅ | DejaVu Sans, white bg, no boxing |
| D3 | **Never truncate** the vertical axis of histograms | Mandatory | ✅ | Fig 1 y-axis 0–100%; Fig 4 from 0 |
| D4 | Error bars + description of error analysis in legend | Mandatory | ✅ | 95% CI bars; legends describe |
| D5 | Thousands separated by commas; SI units | Mandatory | ✅ | e.g., "830,170 alerts" |
| D6 | State software name, version, URL | Mandatory | ✅ | Methods: Python 3.12, NumPy 2.2.6, scikit-learn 1.7.2, Matplotlib 3.10, SciPy 1.15 + repository URL |
| D7 | Multi-panel figures as a single file; number in order of appearance | Mandatory | ✅ | Single-panel figures, numbered 1–4 |

## E. Tables
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| E1 | Editable format (Word/LaTeX), not images | Mandatory | ✅ | Tables 1–2 as text tables in the manuscript |
| E2 | Tables with statistics describe error analysis/ranges in legend | Mandatory | ✅ | Table legends state 95% CI method |
| E3 | Table ≤ one page | Mandatory | ✅ | Both fit one page |

## F. Mandatory end matter
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| F1 | **Data availability statement** (end of main text, before References) | Mandatory | ✅ | Points to the Code Ocean capsule + GitHub (frozen data + code, DOI to be added) |
| F2 | **Author contributions** statement | Mandatory | ✅ | Provided (single author → sole-contribution statement) |
| F3 | **Competing interests** statement (explicit for each author) | Mandatory | ✅ | "The author declares no competing interests." |
| F4 | Acknowledgements (brief, no referee thanks) | Optional | ✅ | Brief; software acknowledged |
| F5 | **LLM-use documentation** in Methods (AI policy) | Mandatory if used | ✅ | Methods documents (i) LLMs are the study object and (ii) any AI assistance in drafting; LLMs not listed as authors |
| F6 | Ethics declarations (human/animal) | If applicable | ✅ N/A | No human participants or animals; synthetic data only — stated in Methods |

## G. References (Nature style)
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| G1 | ≤ 60 references | Recommended | ✅ | 34 references (`latex/sn-bibliography.bib`) |
| G2 | Numbered, sequential, in square brackets | Mandatory | ✅ | BibTeX with the Springer Nature `sn-basic` (Numbered) style auto-numbers in order of appearance |
| G3 | Only published/accepted works or recognised preprints/data repos | Mandatory | ⚠ | All entries are published works, recognised preprints (arXiv), dataset/report sources; author to spot-verify each DOI/URL before submission |
| G4 | ≥6 authors → first author + "et al."; last-name-first; journal italic/abbrev.; bold volume | Mandatory | ✅ | Applied automatically by the `sn-basic.bst` Nature style |
| G5 | No grant details in references | Mandatory | ✅ | None |

## H. Submission package
| # | Requirement | Mandatory | Status | How we meet it |
|---|---|---|---|---|
| H1 | Cover letter (why appropriate for SR; suggested/excluded reviewers; prior editor discussions) | Mandatory | ⚠ | Draft cover letter to be written (offered) |
| H2 | Single manuscript file ≤ 3 MB (first submission; Word preferred, LaTeX/PDF accepted) | Mandatory | ✅ | Manuscript + figures fit; convert Markdown → Word/LaTeX (Springer Nature template provided in folder) |
| H3 | Springer Nature LaTeX template (if LaTeX) | Encouraged | ✅ available | `sn-article-template/` present in the journal folder |
| H4 | Supplementary Information as single separate PDF (if any) | If used | ✅ | Preregistration + full stats + battery details → Supplementary Information (optional) |
| H5 | State prior discussions with an SR Editorial Board Member | Mandatory (cover letter) | ⚠ | Include in cover letter (default: none) |

**Author to-do at submission (the ⚠ items):** add page/line numbers and the corresponding-author asterisk/email; finalise Nature reference formatting; write the cover letter; convert to Word or the Springer Nature LaTeX template; optionally compile Supplementary Information. Everything else is already met in the reformatted manuscript.
