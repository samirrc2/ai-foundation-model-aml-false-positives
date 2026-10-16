#!/usr/bin/env python3
"""Every letter shipped as both PDF and .docx must say the same thing.

check_docx_parity covers the manuscript. The cover letter had no such check, and its .docx was
produced by hand once and never rebuilt, so when the letter changed -- the archive line moved
from the GitHub URL to the Zenodo DOI -- the PDF and the Word file disagreed about where the
data lives. A reviewer opening the .docx would have been sent somewhere the PDF does not
mention. Nothing in the build noticed, because nothing was looking.

Each .tex in paper/ that has BOTH a .pdf and a .docx is compared sentence by sentence, on text
squashed to alphanumerics: the two renderers hyphenate, kern and wrap differently, and page
numbers land mid-sentence in the PDF extraction, none of which is a content difference.

Exit 0 all pairs agree / 1 a pair differs / 2 could not check.
"""
from __future__ import annotations
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"

try:
    import pymupdf
except ImportError:
    print("COULD NOT CHECK: pymupdf not available")
    sys.exit(2)


def squash(t: str) -> str:
    t = re.sub(r"[^a-z0-9]", "", t.lower())
    for lg in ("ffi", "fi", "ff", "fl"):
        t = t.replace(lg, "")
    return t


def pdf_text(p: Path) -> str:
    return "".join(pg.get_text() for pg in pymupdf.open(p))


def docx_text(p: Path) -> str:
    return re.sub(r"<[^>]+>", "", zipfile.ZipFile(p).read("word/document.xml").decode("utf-8"))


pairs = []
for tex in sorted(PAPER.glob("*.tex")):
    stem = tex.stem
    if stem.startswith("_") or stem.startswith("manuscript"):
        continue                      # manuscript pairs are check_docx_parity's job
    pdf, docx = PAPER / f"{stem}.pdf", PAPER / f"{stem}.docx"
    if pdf.exists() and docx.exists():
        pairs.append((stem, pdf, docx))

if not pairs:
    print("COULD NOT CHECK: no letter has both a .pdf and a .docx")
    sys.exit(2)

fails: list[str] = []
checked = 0
for stem, pdf, docx in pairs:
    P, D = squash(pdf_text(pdf)), squash(docx_text(docx))
    if len(P) < 200 or len(D) < 200:
        print(f"COULD NOT CHECK: {stem} renders almost no text (pdf {len(P)}, docx {len(D)})")
        sys.exit(2)
    # sentence-level, from the source so neither renderer defines the truth
    src = re.sub(r"%.*", "", (PAPER / f"{stem}.tex").read_text())
    src = re.sub(r"\\(?:url|href)\{([^}]*)\}", r" \1 ", src)
    src = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", src)
    src = re.sub(r"[{}\\]", " ", src)
    for sent in re.split(r"(?<=[.!?])\s+", src):
        s = squash(sent)
        if len(s) < 40:
            continue
        checked += 1
        in_p, in_d = s in P, s in D
        if in_p != in_d:
            where = "PDF only" if in_p else "docx only"
            fails.append(f"{stem}: sentence appears in the {where}: {sent.strip()[:70]!r}")

print(f"letter pairs checked : {len(pairs)} ({', '.join(p[0] for p in pairs)})")
print(f"sentences compared   : {checked}")
print(f"failed               : {len(fails)}")
for f in fails[:10]:
    print("  " + f)
if fails:
    sys.exit(1)
print("\n  PASS: every letter's PDF and docx carry the same text")
sys.exit(0)
