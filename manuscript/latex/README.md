# LaTeX source (Springer Nature `sn-jnl` template)

Manuscript for *Discover Artificial Intelligence*. Compile with `pdflatex` +
`bibtex` (BibTeX resolves the numbered references):

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Files:

- `main.tex` — the manuscript, using the Springer Nature `sn-jnl` class with the
  `sn-basic` (Numbered) reference style.
- `sn-jnl.cls` — the Springer Nature class (bundled so the source compiles
  standalone, e.g. on Overleaf).
- `sn-basic.bst` — the Nature-style numbered bibliography style.
- `references_discover.bib` — the BibTeX database (all entries cited; DOIs as full
  `https://doi.org/…` links where available).
- `main.bbl` — the pre-generated bibliography (committed so the source also
  compiles without a BibTeX run).
- `fig1_fp_by_model.pdf … fig5_typology_model_heatmap.pdf` — the five figures
  (vector PDF), read by `\includegraphics`.

Verified: compiles with no errors and no undefined references/citations; 43
numbered references; five figures and four tables (Table 4 is the Appendix A
endpoint-aggregation rule).

`build_both.sh` (in this directory) builds both deliverables from this source:
the compiled PDF (`../MANUSCRIPT_Discover_compiled.pdf`) and a Word version
(`../MANUSCRIPT_Discover.docx`, via `build_docx.py`, with the same numbered
citations and embedded figures).

Build artifacts (`*.aux`, `*.log`, `*.out`, `*.blg`, `main.pdf`) are git-ignored.
