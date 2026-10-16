#!/usr/bin/env python3
"""Enforce the Discover Artificial Intelligence submission guidelines that are checkable.

These are the journal's own rules, taken from its submission-guidelines page, and they are the
kind of requirement that drifts silently: nothing in the analysis or the binding gates can see
an abstract that has grown past the word limit, or a table cited out of order. The abstract
limit in particular is a desk-reject trigger -- this manuscript was 299 words against a stated
limit of 250 after the revision added material to it.

Checked here:
  1. ABSTRACT under 250 words.
  2. HEADINGS no more than three levels deep.
  3. TABLES numbered in order of first citation.
  4. FIGURES numbered in order of first citation.
  5. FIGURE CAPTIONS carry no trailing punctuation ("Fig. 1" style, per the guidelines).
  6. Cited REFERENCES carry a DOI or URL -- reported as a count, not a failure, because some
     sources legitimately have neither.

Exit 0 compliant / 1 a rule is broken / 2 could not check.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "manuscript_full.tex"
BBL = ROOT / "paper" / "manuscript_full.bbl"
ABSTRACT_LIMIT = 250
MAX_HEADING_DEPTH = 3

try:
    s = TEX.read_text(encoding="utf-8")
except OSError as e:
    print(f"COULD NOT CHECK: {e}")
    sys.exit(2)
if len(s) < 20000:
    print(f"COULD NOT CHECK: manuscript only {len(s)} chars")
    sys.exit(2)

fails: list[str] = []

# 1 -- abstract length
m = re.search(r"\\abstract\{(.*?)\}\s*\\keywords", s, re.S)
if not m:
    print("COULD NOT CHECK: no \\abstract{...}\\keywords block")
    sys.exit(2)
txt = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", " ", m.group(1))
n_words = len(re.sub(r"[{}$\\]", " ", txt).split())
if n_words >= ABSTRACT_LIMIT:
    fails.append(f"abstract is {n_words} words, limit {ABSTRACT_LIMIT}")

# 2 -- heading depth
depth = 0
for lvl, d in (("section", 1), ("subsection", 2), ("subsubsection", 3), ("paragraph", 4)):
    if re.search(r"\\" + lvl + r"\*?\{", s):
        depth = max(depth, d)
if depth > MAX_HEADING_DEPTH:
    fails.append(f"heading depth {depth} exceeds {MAX_HEADING_DEPTH}")

# 3 and 4 -- float numbering must follow first citation
body = s[s.index(r"\section{Introduction}"):]
def float_order(env, pfx):
    defined = [x.group(1) for x in re.finditer(
        r"\\begin\{" + env + r"\}(?:(?!\\end\{" + env + r"\}).)*?\\label\{(" + pfx + r":[^}]*)\}",
        body, re.S)]
    cited, seen = [], set()
    for x in re.finditer(r"\\ref\{(" + pfx + r":[^}]*)\}", body):
        if x.group(1) not in seen:
            seen.add(x.group(1)); cited.append(x.group(1))
    return defined, cited

for env, pfx, name in (("table", "tab", "tables"), ("figure", "fig", "figures")):
    defined, cited = float_order(env, pfx)
    if defined != cited:
        fails.append(f"{name} are not numbered in order of first citation: "
                     f"document order {defined} against citation order {cited}")

# 5 -- figure captions must not end in punctuation
for x in re.finditer(r"\\begin\{figure\}(?:(?!\\end\{figure\}).)*?\\caption\{(.*?)\}\s*\\label",
                     body, re.S):
    cap = re.sub(r"\s+", " ", x.group(1)).strip()
    if cap.endswith((".", ",", ";", ":")):
        fails.append(f"figure caption ends with punctuation: ...{cap[-56:]!r}")

# 6 -- reference identifiers, reported not enforced
n_refs = n_linked = 0
if BBL.exists():
    items = re.split(r"\\bibitem", BBL.read_text(encoding="utf-8"))[1:]
    n_refs = len(items)
    n_linked = sum(1 for i in items
                   if (chr(92) + "doi{") in i or "doi.org" in i or (chr(92) + "url{") in i or "http" in i)

print(f"abstract words          : {n_words} (limit {ABSTRACT_LIMIT})")
print(f"heading depth           : {depth} (max {MAX_HEADING_DEPTH})")
print(f"cited references        : {n_refs}, carrying a DOI or URL: {n_linked}"
      + (f"  [{n_refs - n_linked} without -- not fatal]" if n_refs else ""))
print(f"failed                  : {len(fails)}")
for f in fails:
    print("  " + f)
if fails:
    sys.exit(1)
print("\n  PASS: the checkable Discover submission requirements are met")
sys.exit(0)
