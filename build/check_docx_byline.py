#!/usr/bin/env python3
"""Every manuscript .docx must name its authors.

The journal returned this submission because manuscript_full.docx carried the title and the
abstract and no author names at all. pandoc had silently dropped Springer's \\author macros,
the PDF was unaffected, and all ten existing gates passed: check_docx_parity compares body
SENTENCES, and a byline is not a sentence in the source, so parity is blind to it by
construction. Nothing in the repository read the byline, so nothing could miss it.

Exit 0 every author named, 2 if any is missing OR the check could not run. "Could not check"
is never 0 -- a .docx that cannot be opened is reported, not passed over.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from byline import authors_in, docx_head, missing_authors   # noqa: E402

PB = Path(__file__).resolve().parents[1]
PAPER = PB / "paper"

# (.docx, the source its byline must come from). The cover letter is signed, not bylined, and
# is covered by check_letter_parity instead.
PAIRS = [("manuscript_full.docx", "manuscript_full.tex"),
         ("manuscript_full_tracked.docx", "_marked.tex")]

failed = checked = 0
print("== docx byline ==")
for docx_name, tex_name in PAIRS:
    docx, tex = PAPER / docx_name, PAPER / tex_name
    if not docx.exists():
        print(f"  COULD NOT CHECK: {docx_name} absent")
        failed += 1
        continue
    if not tex.exists():
        # _marked.tex is a gitignored build intermediate, so a clone legitimately lacks it.
        # Fall back to the manuscript source: the tracked copy carries the same authors.
        tex = PAPER / "manuscript_full.tex"
        if not tex.exists():
            print(f"  COULD NOT CHECK: no source for {docx_name}")
            failed += 1
            continue
    src = tex.read_text()
    people = authors_in(src)
    if not people:
        print(f"  COULD NOT CHECK: no \\author in {tex.name}")
        failed += 1
        continue
    try:
        missing = missing_authors(docx, src)
        head = docx_head(docx, 300)
    except Exception as exc:                        # noqa: BLE001 - report, do not mask
        print(f"  COULD NOT CHECK: {docx_name} unreadable: {exc}")
        failed += 1
        continue
    checked += 1
    if missing:
        print(f"  FAIL {docx_name}: no byline for {', '.join(missing)}")
        print(f"       opens: {head[:120].strip()}")
        failed += 1
    else:
        print(f"  ok   {docx_name}: {', '.join(n for n, _, _ in people)}")

print(f"\n  docx checked : {checked}")
print(f"  failed       : {failed}")
if failed:
    print("\n  FAIL: a manuscript .docx is missing author names -- do NOT submit it")
    sys.exit(2)
print("\n  PASS: every manuscript .docx names all of its authors")
