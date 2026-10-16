#!/usr/bin/env python3
"""Confirm the committed results/ are exactly what the frozen inputs produce.

Fault injection bent a value in results/aggregation_sensitivity.json that the manuscript does
not print -- a single-call miss rate -- and no gate reported it. The document gates cannot: by
construction they only look at numbers the paper quotes. And reproduce.sh does not report it
either, because it REGENERATES results/ and so silently repaired the bent value, printing
REPRODUCIBLE and exiting 0. The tampered number was corrected rather than flagged.

That leaves a real gap for a deposit that ships results/ as committed artifacts. Anyone reading
the shipped files without re-running the analysis sees whatever is in them, and a value the
manuscript never quotes can drift with nothing to catch it.

So this gate asks the question reproduce.sh cannot: having regenerated results/ from the frozen
inputs, does the committed copy still match? git answers it. Any staged or unstaged difference
under results/ means the committed artifacts are not what the code produces, and the fix is to
commit the regenerated output (or to find out why it changed).

Run this AFTER reproduce.sh, which build_all.sh does. Exit 0 clean / 1 drift / 2 could not check.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

if not RESULTS.is_dir():
    print("COULD NOT CHECK: no results/ directory")
    sys.exit(2)
if not (ROOT / ".git").exists():
    # The capsule track ships code + data with no repository, so there is nothing to compare
    # the committed copy against. That is a skip, and it must not read as a pass.
    print("COULD NOT CHECK: not a git repository (capsule track ships no .git)")
    sys.exit(2)

try:
    p = subprocess.run(["git", "status", "--porcelain", "--", "results"],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
except (OSError, subprocess.SubprocessError) as e:
    print(f"COULD NOT CHECK: {e}")
    sys.exit(2)
if p.returncode != 0:
    print(f"COULD NOT CHECK: git status failed: {p.stderr.strip()}")
    sys.exit(2)

drift = [ln for ln in p.stdout.splitlines() if ln.strip()]
tracked = sum(1 for _ in RESULTS.rglob("*") if _.is_file())

print(f"result files present   : {tracked}")
print(f"differ from committed  : {len(drift)}")
for ln in drift[:20]:
    print("  " + ln)
if drift:
    print("\n  The committed results/ are not what the frozen inputs produce. Re-run "
          "reproduce.sh and commit the output, or explain the difference.")
    sys.exit(1)
print("\n  PASS: every committed result file matches the regenerated output")
sys.exit(0)
