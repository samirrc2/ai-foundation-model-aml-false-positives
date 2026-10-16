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
# Run every gate and report by name. "| tail -1" alone would print a summary line while
# discarding the rule that failed, and a gate's exit 2 (could not check) must be visible as
# something other than a pass -- so capture the output, keep the code, and say which it was.
gate_fail=0
for g in check_binding check_coverage check_table_agg check_verbatim \
         check_docx_citations check_docx_parity; do
  out="$("$PY" "build/$g.py" 2>&1)" && rc=0 || rc=$?
  case "$rc" in
    0) printf '   %-22s PASS  %s\n' "$g" "$(printf '%s' "$out" | tail -1)" ;;
    2) printf '   %-22s SKIPPED (could not check)\n' "$g"; printf '%s\n' "$out" | sed 's/^/      /'
       gate_fail=1 ;;
    *) printf '   %-22s FAIL (exit %s)\n' "$g" "$rc"; printf '%s\n' "$out" | sed 's/^/      /'
       gate_fail=1 ;;
  esac
done
[ "$gate_fail" -eq 0 ] || { echo "GATES FAILED"; exit 1; }

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
