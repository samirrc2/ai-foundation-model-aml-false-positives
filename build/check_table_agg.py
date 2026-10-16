"""Table 5 is a hand-typed duplicate of a generated result. Gate every cell, not a sample.

The aggregation-sensitivity table carries 9 rows x 6 columns = 54 numbers, each of which also
exists in results/aggregation_sensitivity.json. Anchored binding rules are the right instrument
for a number in a sentence, but writing 54 of them is unmaintainable, and the previous round of
fault injection proved the cost of sampling instead: bending a single single-call cell to
0.4242 passed every gate, because only five of the 54 cells had a rule.

So this gate reconstructs each row from the JSON and compares it cell by cell against the
table as typed. Any single-cell drift fails, and so does a row whose label was reworded away
from the policy it reports -- which is the table's version of a bound sentence being edited.

Exit 0 all cells match / 1 a cell or row differs / 2 could not check.
"""
from __future__ import annotations
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "manuscript_full.tex"
RES = ROOT / "results" / "aggregation_sensitivity.json"

# Column order as the table prints it, mapped to the model keys the JSON uses.
COLS = ["Gemini Flash", "GPT-4o", "GPT-4.1-mini", "Gemini Flash-Lite", "GPT-4o-mini"]

# Row label as typed -> where its numbers come from. A label the table no longer contains is a
# failure, not a skip: the row was renamed or deleted and nothing else would notice.
ROWS = [
    ("Ties to flag (preregistered D4, primary)", "policies", "ties_to_flag_preregistered_D4"),
    ("Ties to no flag (strict majority)",        "policies", "ties_to_no_flag_strict_majority"),
    ("Ties as abstentions (dropped)",            "policies", "ties_as_abstention"),
    ("Unanimity required to flag",               "policies", "unanimity_required"),
    ("Label-dependent (as submitted)",           "policies", "label_dependent_as_published"),
    ("Single call: FATF prompt seed 0",  "single_call_configurations", "v_fatf|seed0"),
    ("Single call: FATF prompt seed 1",  "single_call_configurations", "v_fatf|seed1"),
    ("Single call: terse prompt seed 0", "single_call_configurations", "v_terse|seed0"),
    ("Single call: terse prompt seed 1", "single_call_configurations", "v_terse|seed1"),
]


def hu(x: float, nd: int = 1) -> str:
    """Half-up. format() is round-half-even and would print a true 24.45 as "24.4"."""
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


try:
    tex = TEX.read_text()
    ag = json.loads(RES.read_text())
except OSError as e:
    print(f"COULD NOT CHECK: {e}")
    sys.exit(2)

# Isolate the table body so a stray "&" elsewhere in the manuscript cannot be read as a cell.
m = re.search(r"\\label\{tab:agg\}(.*?)\\botrule", tex, flags=re.S)
if not m:
    print("COULD NOT CHECK: tab:agg not found (label renamed or table removed)")
    sys.exit(2)
body = m.group(1)
# Strip the horizontal rules before splitting. They sit on the same source line as the row that
# follows them, so a row right after \midrule would otherwise look like a LaTeX command and be
# skipped -- silently dropping the primary D4 row, the most load-bearing row in the table.
body = re.sub(r"\\(?:top|mid|bottom|cmid)rule\b|\\hline\b", " ", body)

typed: dict[str, list[str]] = {}
for line in body.split(r"\\"):
    cells = [c.strip() for c in line.split("&")]
    if len(cells) == 7 and cells[0] and not cells[0].startswith("\\"):
        label = re.sub(r"\s+", " ", cells[0].replace("\\ ", " ")).strip()
        typed[label] = cells[1:]

fails: list[str] = []
checked = 0
for label, section, key in ROWS:
    if label not in typed:
        fails.append(f"ROW MISSING  '{label}' is not in the table as typed")
        continue
    src = ag.get(section, {}).get(key)
    if src is None:
        fails.append(f"NO SOURCE    '{label}' -> {section}.{key} absent from results JSON")
        continue
    want = [hu(src["per_model"][c]["fp_rate"] * 100) for c in COLS]
    want.append(hu(src["fp_spread_pp"]))
    got = typed[label]
    for col, (w, g) in enumerate(zip(want, got)):
        checked += 1
        if w != g:
            name = (COLS + ["Spread"])[col]
            fails.append(f"CELL         '{label}' / {name}: table says {g}, data says {w}")

if checked == 0:
    print("COULD NOT CHECK: parsed no cells from tab:agg")
    sys.exit(2)

print(f"table 5 cells checked : {checked}")
print(f"failed                : {len(fails)}")
for f in fails:
    print("  " + f)
sys.exit(1 if fails else 0)
