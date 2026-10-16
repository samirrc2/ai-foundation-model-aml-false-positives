#!/usr/bin/env python3
"""Verify the tracked .docx actually carries its marks.

This guards a silent failure with a specific history. pandoc does not know soul's \\texthl, so
it DROPS \\HLtext without any warning and exits 0. A tracked document built that way contains
the final text with every addition unmarked -- it looks like a clean manuscript, opens without
complaint, and tells the editor nothing about what changed. make_docx.py rewrites \\HLtext,
\\HLcode and \\HLhead to \\hl and \\HLdel to \\sout for exactly this reason, and this gate proves
the rewrite is still working rather than assuming it.

Four checks:
  1. The docx exists and carries BOTH highlight runs (additions) and strikethrough runs
     (deletions). Either count at zero means a whole class of mark was lost.
  2. Known added text is present, known deleted text is present. The tracked copy must contain
     the deletions too, since that is what distinguishes it from the clean manuscript.
  3. The legend is present, so a reader knows what the colours mean.
  4. The tracked body is longer than the clean one, because it re-inserts deleted runs.

Comparison is on text squashed to alphanumerics, because the PDF and docx renderers hyphenate
and kern differently -- "captured" extracts as "cap-\\ntured" from the PDF, which is a rendering
artifact and not a missing sentence.

Exit 0 pass, 1 fail, 2 could not check.
"""
from __future__ import annotations
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKED = ROOT / "paper" / "manuscript_full_tracked.docx"
CLEAN = ROOT / "paper" / "manuscript_full.docx"
MARKED_TEX = ROOT / "paper" / "_marked.tex"

for f in (TRACKED, CLEAN):
    if not f.exists():
        print(f"COULD NOT CHECK: {f.name} missing (run build/make_docx.py)")
        sys.exit(2)


def body(path: Path) -> tuple[str, str]:
    try:
        xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    except (zipfile.BadZipFile, KeyError) as e:
        print(f"COULD NOT CHECK: {path.name} is not a readable docx: {e}")
        sys.exit(2)
    return xml, re.sub(r"<[^>]+>", "", xml)


def squash(t: str) -> str:
    t = re.sub(r"[^a-z0-9]", "", t.lower())
    for lg in ("ffi", "fi", "ff", "fl"):
        t = t.replace(lg, "")
    return t


xml, text = body(TRACKED)
_, clean_text = body(CLEAN)
S, C = squash(text), squash(clean_text)

n_hl = len(re.findall(r"<w:highlight[^/>]*/>", xml))
n_st = len(re.findall(r"<w:strike[^/>]*/>", xml))

fails: list[str] = []
if n_hl == 0:
    fails.append("no highlight runs: every ADDITION was dropped (the pandoc \\texthl failure)")
if n_st == 0:
    fails.append("no strikethrough runs: every DELETION was dropped")

# Added in this revision, and deleted in this revision. Both must survive into the docx.
ADDED = ["Only the alias strings were captured",
         "36- to 196-fold",
         "AC1 instead averaged 0.924"]
DELETED = ["rather than inferred from the alias"]
LEGEND = "Marked copy, revision 1"

for s in ADDED:
    if squash(s) not in S:
        fails.append(f"added text absent from the tracked docx: {s[:52]!r}")
for s in DELETED:
    if squash(s) not in S:
        fails.append(f"deleted text absent from the tracked docx: {s[:52]!r}")
    if squash(s) in C:
        fails.append(f"deleted text still present in the CLEAN docx: {s[:52]!r}")
if squash(LEGEND) not in S:
    fails.append("the marked-copy legend is missing, so the colours are unexplained")
if len(S) <= len(C):
    fails.append(f"tracked body ({len(S)} chars) is not longer than clean ({len(C)}); "
                 f"it must be, because it re-inserts deleted runs")

# Cross-check the counts against the source, so a partial drop is visible too.
if MARKED_TEX.exists():
    src = MARKED_TEX.read_text(encoding="utf-8")
    want_hl = len(re.findall(r"\\HL(?:text|code|head)\{", src))
    want_st = len(re.findall(r"\\HLdel\{", src))
    if want_st and n_st < want_st * 0.5:
        fails.append(f"only {n_st} strikethrough runs for {want_st} \\HLdel in the source")
    print(f"source marks           : {want_hl} added, {want_st} deleted")

print(f"docx highlight runs    : {n_hl}")
print(f"docx strikethrough runs: {n_st}")
print(f"tracked vs clean chars : {len(S)} vs {len(C)}")
print(f"failed                 : {len(fails)}")
for f in fails:
    print("  " + f)
if fails:
    sys.exit(1)
print("\n  PASS: the tracked docx carries its additions, deletions and legend")
sys.exit(0)
