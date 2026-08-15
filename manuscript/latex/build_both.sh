#!/usr/bin/env bash
# Build BOTH deliverables from the single LaTeX source (main.tex):
#   ../MANUSCRIPT_Discover_compiled.pdf   (Springer sn-jnl, numbered refs)
#   ../MANUSCRIPT_Discover.docx           (Word, same numbering, embedded figures)
# Run from the latex/ directory.
set -e
cd "$(dirname "$0")"

echo "== [1/2] PDF =="
rm -f main.aux main.bbl main.blg 2>/dev/null || true   # non-fatal: some mounts block delete
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
bibtex main >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
cp main.pdf ../MANUSCRIPT_Discover_compiled.pdf
echo "   PDF -> ../MANUSCRIPT_Discover_compiled.pdf"

echo "== [2/2] DOCX =="
python3 build_docx.py
echo "   DOCX -> ../MANUSCRIPT_Discover.docx"
echo "Done."
