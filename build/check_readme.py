#!/usr/bin/env python3
"""Check that the paths README.md and the reproducibility document tell a reader to use exist.

This gate was written because both documents still described the Code Ocean layout after the
repository was flattened for the Zenodo deposit. The quick start said

    cd ai-foundation-model-aml-false-positives/capsule
    pip install -r code/requirements.txt

and neither path had existed for some time. Every numeric gate passed throughout: a wrong path
is not a wrong number, so nothing in the suite could see it. A reviewer following the
instructions would have failed on the first command.

Two checks, both narrow on purpose. A noisy documentation gate gets ignored, which is worse
than no gate.

1. SLASH-QUALIFIED PATHS. Any `dir/file.ext` in a backtick span or a \\pc{...} macro must
   resolve from the repository root. Bare basenames are deliberately NOT checked: the documents
   legitimately name `altrisk.py` in prose while the file lives at `analysis/altrisk.py`, and
   demanding a directory everywhere would mean rewriting prose to satisfy a checker.

2. QUICK-START COMMANDS. The `pip install -r <file>`, `bash <script>` and `cd <dir>` lines
   inside fenced blocks must name things that exist. These are the lines a reviewer runs
   verbatim, so they get checked as commands rather than as prose.

Exit 0 all resolve / 1 something does not / 2 could not check.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ["README.md", "REPRODUCIBILITY_DOCUMENTATION.tex"]
EXEMPT_FILE = ROOT / "build" / "readme_path_exemptions.json"

try:
    bodies = {d: (ROOT / d).read_text(encoding="utf-8") for d in DOCS}
except OSError as e:
    print(f"COULD NOT CHECK: {e}")
    sys.exit(2)
for d, b in bodies.items():
    if len(b) < 2000:
        print(f"COULD NOT CHECK: {d} is only {len(b)}B")
        sys.exit(2)

exempt: dict[str, str] = {}
if EXEMPT_FILE.exists():
    try:
        exempt = json.loads(EXEMPT_FILE.read_text())
    except ValueError as e:
        print(f"COULD NOT CHECK: {EXEMPT_FILE.name} is not valid JSON: {e}")
        sys.exit(2)


def unescape_tex(t: str) -> str:
    # \pc{build\_battery.py} -> build_battery.py. Without this every underscored filename in
    # the LaTeX document reads as a different, non-existent path.
    return t.replace("\\_", "_").replace("\\%", "%").replace("\\&", "&").replace("\\#", "#")


SLASH_PATH = re.compile(r"^(?:[\w.-]+/)+[\w.-]+$")

# The layout tables write a path relative to the section they sit in -- "battery/full.jsonl"
# under a data/ heading, "baselines.json" in a results column -- so a reference resolves
# against any of these roots. Stale layout paths still fail: "code/requirements.txt" and
# "manuscript/latex/" resolve under none of them.
ROOTS = [ROOT, ROOT / "data", ROOT / "results", ROOT / "paper"]


def resolves(rel: str) -> bool:
    return any((r / rel).exists() for r in ROOTS)
# A path ending in "/" names a directory; one with an extension names a file. Globs and shell
# brace expansions ("results/table{1,2}.csv") are skipped: they describe a set, not a path.
SKIP = re.compile(r"[*?{}$<>|\s]|\.\.\.")


def candidates(doc: str, body: str):
    if doc.endswith(".tex"):
        spans = [unescape_tex(m.group(1)) for m in re.finditer(r"\\(?:pc|code|texttt)\{([^{}]*)\}", body)]
        spans += [unescape_tex(m.group(1)) for m in re.finditer(r"\\verb\|([^|]*)\|", body)]
    else:
        spans = [m.group(1) for m in re.finditer(r"`([^`\n]+)`", body)]
    # Fenced blocks too. The pipeline diagram names its outputs as bare paths rather than in
    # backticks, and renaming one there (results/correlated_miss.json ->
    # results/correlated_misses.json) passed while only backtick spans were scanned.
    fenced = re.findall(r"```[a-z]*\n(.*?)```", body, flags=re.S)
    fenced += re.findall(r"\\begin\{verbatim\}(.*?)\\end\{verbatim\}", body, flags=re.S)
    for blk in fenced:
        blk = unescape_tex(blk) if doc.endswith(".tex") else blk
        for tok in re.findall(r"[\w.{}*\[\]-]*(?:/[\w.{}*\[\]-]+)+", blk):
            spans.append(tok)
    for s in spans:
        s = s.strip().rstrip(",.;:")
        if SKIP.search(s) or not s:
            continue
        yield s


fails: list[str] = []
checked = 0

for doc, body in bodies.items():
    for s in candidates(doc, body):
        bare = s.rstrip("/")
        if not SLASH_PATH.match(bare):
            continue
        # A real path reference either names a directory (trailing "/") or ends in a segment
        # with an extension. This drops prose that merely contains slashes
        # ("precision/recall/specificity/F1/MCC", "table1/table2") and the reader's own
        # ".venv/bin/activate", none of which are repository paths, without needing an
        # exemption entry for each.
        if not s.endswith("/") and "." not in bare.rsplit("/", 1)[-1]:
            continue
        if bare in exempt or s in exempt:
            continue
        checked += 1
        if not resolves(bare):
            fails.append(f"NO SUCH PATH  {doc}: '{s}'")

# Quick-start commands, inside fenced blocks only.
CMDS = [
    (re.compile(r"pip install -r\s+([\w./-]+)"), "pip install -r"),
    (re.compile(r"bash\s+([\w./-]+\.sh)"), "bash"),
    (re.compile(r"python3?\s+(-m\s+\w+|[\w./-]+\.py)"), "python"),
]
for doc, body in bodies.items():
    blocks = re.findall(r"```[a-z]*\n(.*?)```", body, flags=re.S)
    blocks += re.findall(r"\\begin\{verbatim\}(.*?)\\end\{verbatim\}", body, flags=re.S)
    for blk in blocks:
        blk = unescape_tex(blk) if doc.endswith(".tex") else blk
        for line in blk.splitlines():
            line = line.split("#")[0].strip()
            for rx, what in CMDS:
                for m in rx.finditer(line):
                    tgt = m.group(1)
                    if tgt.startswith("-m ") or tgt in exempt:
                        continue
                    checked += 1
                    if not resolves(tgt):
                        fails.append(f"NO SUCH PATH  {doc}: `{what} {tgt}` in a quick-start block")
            # "cd <repo>/<sub>" must name a directory that exists inside the repo. The repo's own
            # name is the clone target, so only the part after it is checkable.
            cd = re.match(r"cd\s+([\w./-]+)$", line)
            if cd:
                parts = cd.group(1).split("/", 1)
                if len(parts) == 2 and parts[1] and parts[1] not in exempt:
                    checked += 1
                    if not (ROOT / parts[1]).is_dir():
                        fails.append(
                            f"NO SUCH PATH  {doc}: `cd .../{parts[1]}` -- no such directory "
                            f"(the repository is flat, there is no sub-directory to enter)")

if checked == 0:
    print("COULD NOT CHECK: extracted no paths from the documentation")
    sys.exit(2)

print(f"documented paths checked : {checked}")
print(f"failed                   : {len(fails)}")
for f in fails:
    print("  " + f)
sys.exit(1 if fails else 0)
