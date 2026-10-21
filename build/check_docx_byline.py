#!/usr/bin/env python3
"""Every manuscript .docx must carry correct front matter: authors, and the live keywords.

The journal returned this submission because manuscript_full.docx carried the title and the
abstract and no author names at all. pandoc had silently dropped Springer's \\author macros,
the PDF was unaffected, and all ten existing gates passed: check_docx_parity compares body
SENTENCES, and a byline is not a sentence in the source, so parity is blind to it by
construction. Nothing in the repository read the byline, so nothing could miss it.

The keyword check was added for the same reason, one fault later: _marked.tex carries TWO
\\keywords blocks, because the marking tool splices the superseded round-1 list into the
abstract inside \\HLdel{}. make_docx.py took the first with re.search, so the tracked .docx
advertised round-1 keywords while the tracked PDF showed the current ones. No gate saw it.

Exit 0 when every author is named and the keywords match the source, 2 if anything is missing
OR the check could not run. "Could not check" is never 0 -- a .docx that cannot be opened is
reported, not passed over.
"""
import re
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
    # the live \keywords is the LAST one; earlier ones are deletions inside \HLdel{}
    kw = re.findall(r'\\keywords\{([^}]*)\}', src)
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
    if kw:
        # Inspect the Keywords LINE only. A whole-document scan false-fails, because terms from
        # the superseded list -- "anti-money laundering", "model risk", "foundation models" --
        # are ordinary prose that appears legitimately in the abstract.
        body = docx_head(docx, 8000)
        m = re.search(r'Keywords:\s*(.{0,400})', body)
        if not m:
            print(f"  FAIL {docx_name}: no Keywords line")
            failed += 1
        else:
            want = [w.strip() for w in kw[-1].split(',') if w.strip()]
            # The Keywords line must BEGIN with the live list, joined as the source writes it.
            # Two weaker tests were tried first and both false-failed on correct output:
            # a substring scan matched "model risk" inside "AI model risk management", and
            # exact comma-field equality broke on the final term, which runs into the heading
            # that follows it with no comma between.
            # startswith is necessary AND sufficient: if the line opens with exactly the live
            # list, no superseded term can be in it. A separate stale-term scan was tried and
            # only produced false failures, matching "model risk" inside the live term
            # "AI model risk management".
            line = re.sub(r'\s+', ' ', m.group(1)).strip()
            joined = ', '.join(want)
            if not line.startswith(joined):
                print(f"  FAIL {docx_name}: Keywords line does not match the source")
                print(f"       want: {joined[:110]}")
                print(f"       got : {line[:len(joined)][:110]}")
                failed += 1
            else:
                print(f"       keywords ok ({len(want)} terms)")

print(f"\n  docx checked : {checked}")
print(f"  failed       : {failed}")
if failed:
    print("\n  FAIL: a manuscript .docx has wrong front matter -- do NOT submit it")
    sys.exit(2)
print("\n  PASS: every manuscript .docx names all authors and carries the live keywords")
