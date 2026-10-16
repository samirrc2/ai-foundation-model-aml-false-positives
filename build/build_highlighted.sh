#!/usr/bin/env bash
# Build manuscript_full_tracked.pdf: the revised manuscript with every change marked, for the
# editor and referees comparing against the version they read at original submission.
#
# Marking is done by build/mark_changes.py, which marks the FINAL manuscript in place rather
# than letting a tool re-emit the document. See that file's docstring for the three latexdiff
# configurations that were tried first and why each was rejected -- the last of them compiled
# cleanly while silently dropping 19 table captions, 3 section headings and two pages.
#
# build/check_marked.py then proves the marking is content-preserving by stripping the markup
# and requiring a byte-identical round-trip to manuscript_full.tex. The build FAILS if that does not hold.
#
#   bash build/build_highlighted.sh            # baseline: paper/manuscript_round1_baseline.tex
#   bash build/build_highlighted.sh <file>     # baseline: another .tex
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"

BASE="${1:-paper/manuscript_round1_baseline.tex}"
NEW="paper/manuscript_full.tex"
STEM="_marked"
OUT="paper/manuscript_full_tracked.pdf"

[ -f "$BASE" ] || { echo "ERROR: baseline '$BASE' not found" >&2; exit 3; }
# A diff against an identical file yields a mark-free PDF and still exits 0: the failure mode
# that looks like success.
cmp -s "$BASE" "$NEW" && { echo "ERROR: baseline is identical to the manuscript" >&2; exit 3; }
[ -f "paper/manuscript_full.pdf" ] || { echo "ERROR: build manuscript_full.pdf first (check_marked compares against it)" >&2; exit 3; }

python3 build/mark_changes.py "$BASE" "$NEW" "paper/$STEM.tex"

# Each pass is capped. An earlier markup bug sent pdflatex into a loop at 100% CPU for 15
# minutes; -interaction=nonstopmode does not help, because the loop is in macro expansion
# rather than at an error prompt.
run_tex() { perl -e 'alarm 180; exec @ARGV' pdflatex -interaction=nonstopmode "$1" >/dev/null 2>&1 || true; }
# Fixed passes, matching build_all.sh. Paper 3's version looped until the .aux "lastpage"
# field agreed with the real page count, but this document class never writes that field, so
# the grep found nothing, the assignment failed under "set -e pipefail", and the script aborted
# with exit 1 after having produced a perfectly good PDF -- a failure that looked like a
# LaTeX error and was not one.
(
  cd paper
  for i in 1 2; do run_tex "$STEM.tex"; done
  bibtex "$STEM" >/dev/null 2>&1 || true
  for i in 1 2 3; do run_tex "$STEM.tex"; done
)
[ -f "paper/$STEM.pdf" ] || { echo "   FAILED: no PDF produced" >&2
  grep -E '^! ' "paper/$STEM.log" | head -6 >&2 || true; exit 1; }

ERRS=$(grep -cE '^! ' "paper/$STEM.log" || true)
[ "$ERRS" -eq 0 ] || { echo "   FAILED: $ERRS LaTeX errors" >&2
  grep -nE '^! ' "paper/$STEM.log" | head -6 >&2; exit 1; }

python3 build/check_marked.py || { echo "   FAILED: marked copy did not verify" >&2; exit 1; }

cp "paper/$STEM.pdf" "$OUT"
grep -o "Output written on $STEM.pdf ([0-9]* pages" "paper/$STEM.log" | head -1 | sed 's/^/   /' || true
echo "   -> $OUT"
rm -f paper/$STEM.aux paper/$STEM.log paper/$STEM.out paper/$STEM.bbl paper/$STEM.blg paper/$STEM.spl
