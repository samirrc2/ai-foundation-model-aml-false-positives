# LaTeX source (Springer Nature template)

Compile with pdflatex (two passes for cross-references and citations):

```bash
pdflatex main.tex
pdflatex main.tex
```

- `main.tex` — the manuscript, using the Springer Nature `sn-jnl` class with the
  `sn-basic` (Numbered) reference style and the `lineno` option (line numbers in
  the margin, as recommended by Scientific Reports).
- `sn-jnl.cls` — the Springer Nature class (bundled so the source compiles
  standalone, e.g. on Overleaf).
- `fig1_fp_by_model.pdf … fig4_typology_miss.pdf` — the four figures (vector PDF),
  read by `\includegraphics`.

The manuscript uses a **manual `thebibliography`** environment, so **no BibTeX run
and no `.bst` file are required**. Verified: `main.tex` compiles with `pdflatex`
alone, with no errors or undefined references, to a 12-page PDF.

Build artifacts (`*.aux`, `*.log`, `*.out`, `main.pdf`, preview PNGs, `bst/`) are
git-ignored; delete them locally before a raw archive if desired.
