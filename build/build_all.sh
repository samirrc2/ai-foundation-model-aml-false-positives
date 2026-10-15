#!/usr/bin/env bash
# Rebuild every deliverable from source, then run every gate.
#
# One entry point so the manuscript PDF, its .docx companion and the response letter cannot
# drift apart: each is produced here, in order, and nothing is copied by hand.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"
PY="${PY:-python3}"

run_tex() { perl -e 'alarm 180; exec @ARGV' pdflatex -interaction=nonstopmode "$1" >/dev/null 2>&1 || true; }

echo "== 1. analysis (frozen inputs -> results/)"
bash reproduce.sh >/dev/null
echo "   results regenerated and verified byte-identical"

echo "== 2. manuscript"
( cd paper
  for i in 1 2; do run_tex manuscript_full.tex; done
  bibtex manuscript_full >/dev/null 2>&1 || true
  for i in 1 2; do run_tex manuscript_full.tex; done )
ERR=$(grep -cE '^! ' paper/manuscript_full.log || true)
[ "$ERR" -eq 0 ] || { echo "   FAILED: $ERR TeX errors"; grep -nE '^! ' paper/manuscript_full.log | head -5; exit 1; }

echo "== 3. response letter and cover letter"
( cd paper
  for f in response_to_reviewers cover_letter response_to_editor; do
    [ -f "$f.tex" ] && { for i in 1 2; do run_tex "$f.tex"; done; }
  done )

echo "== 4. docx companion"
"$PY" build/make_docx.py | sed 's/^/   /'

echo "== 5. gates"
"$PY" build/check_binding.py        | tail -1
"$PY" build/check_verbatim.py       | tail -1
"$PY" build/check_docx_citations.py | tail -1
"$PY" build/check_docx_parity.py    | tail -1

echo "== 6. clean artefacts"
find paper -maxdepth 1 \( -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.blg" -o -name "*.spl" \) -delete

echo "== 7. every deliverable, by content"
"$PY" - <<'PYX'
import re, hashlib, os
from pypdf import PdfReader
TARGETS = ["paper/manuscript_full.pdf", "paper/response_to_reviewers.pdf",
           "paper/cover_letter.pdf", "paper/response_to_editor.pdf"]
for f in TARGETS:
    if not os.path.exists(f):
        print(f"   {'--':>5}  {'-'*10}  ABSENT {f}"); continue
    n = len(PdfReader(f).pages)
    sha = hashlib.sha256(open(f, "rb").read()).hexdigest()[:10]
    print(f"   {n:3d}pp  {sha}  OK     {f}")
PYX
