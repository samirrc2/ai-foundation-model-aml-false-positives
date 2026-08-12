# RUNBOOK — P4

Exact commands. **CAPTURE runs on your local machine** (where the API keys and
network live); Cowork's sandbox cannot reach the vendor APIs. **ANALYSIS runs
anywhere for $0.** Nothing beyond the pilot runs until the pilot passes and you
say go.

Prereqs (local):
```bash
cd "NIW/Paper 4"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# keys are read from ../API Keys/keys.env.txt automatically (OPENAI_API_KEY_1..,
# GEMINI_API_KEY_1.., XAI_API_KEY). The Anthropic key is intentionally blank/unused.
```

### TL;DR — run the pilot (copy-paste)
```bash
cd "NIW/Paper 4"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

PILOT_MOCK=1 ./run_all.sh                 # 1. dry-run: proves it works for $0 → PILOT: PASS
python3 capture/probe.py --subgrid pilot  # 2. confirm models resolve (tiny real spend)
RESET=1 SUBGRID=pilot ./run_all.sh        # 3. the real pilot: ≤$10, ledger-gated, resumable
cat pilot/PILOT_VERDICT.md                # 4. read the verdict, then stop for go-ahead
```
That's the whole pilot. Steps 1–4, in order. Nothing spends real money until step 2.

---

## 0. Offline dry-run — prove the pipeline for $0 (do this first, anywhere)
Deterministic fake screener, no network, no spend. Must end in `PILOT: PASS`.
```bash
PILOT_MOCK=1 ./run_all.sh
# also verifiable piecemeal:
python3 capture/build_battery.py                 # battery (offline, $0), SHA-256 frozen
python3 capture/ledger_selftest.py               # proves the hard $10 cap aborts
```
Expected: `PILOT: PASS → cleared for full run`, 3,840 rows, 0 ERROR, spend $0.0000.

---

## (a) Pre-flight / probe — confirm models resolve + measure real per-call price
One tiny live call per pilot model → served-model fingerprint + measured price into
`manifest/probe_receipts.json`. Fixes the provisional snapshot strings in
`config/models.yaml` if any 404. Tiny real spend (fractions of a cent).
```bash
python3 capture/probe.py --subgrid pilot
# if a model errors, edit config/models.yaml api_model to the current snapshot,
# log it in DECISIONS.md, and re-probe.
```

Optional pre-flight cost check (no calls made):
```bash
for m in openai_4o_mini openai_41_mini gemini_flash gemini_flash_lite; do
  for v in v_terse v_fatf; do
    python3 capture/orchestrator.py --subgrid pilot --model $m --variant $v --dry-run
  done
done
# each prints projected worst-case spend vs the $10 cap and refuses if over.
```

---

## (b) The real pilot — ≤ $10, ledger-gated (spends money)

> **First real run:** clear the offline dry-run's MOCK artifacts once, or capture
> will refuse on a MOCK/REAL mode mismatch:
> ```bash
> RESET=1 SUBGRID=pilot ./run_all.sh        # clears mock CSVs/receipts/ledger, then runs the REAL pilot
> ```
> (`RESET=1` only clears when you ask; REAL captures are otherwise append-only.)

The global ledger enforces `$10` across ALL captures; it hard-aborts the instant
projected-or-actual cumulative spend would cross the cap, and pre-flight refuses to
start an over-budget run. Resumable: re-run to continue; completed cells are never
re-billed.
```bash
./run_all.sh                    # SUBGRID defaults to pilot; CONC defaults to 5
# equivalently, one model/variant at a time (same global ledger):
python3 capture/orchestrator.py --subgrid pilot --model openai_4o_mini --variant v_terse
python3 capture/freeze.py       --subgrid pilot --model openai_4o_mini --variant v_terse
# ... repeat for each (model, variant) ...
```
If the ledger trips: the run stops cleanly and prints the spend; just re-run to
resume. A capture with > 2% ERROR is non-authoritative — `freeze.py` will refuse
to freeze it; re-run those cells first.

---

## (c) Analysis + verdict — pure, $0, reproducible
Reads frozen CSVs only; byte-identical on re-run.
```bash
python3 analysis/run.py --subgrid pilot          # -> claims.json (every cited number + CI)
python3 pilot/verdict.py                          # -> pilot/PILOT_VERDICT.md, PILOT_RESULTS.md
```
Read `pilot/PILOT_VERDICT.md`. It ends in exactly one of:
`PILOT: PASS → cleared for full run` / `PILOT: FAIL (...)` / `PILOT: KILL (...)`.

**Then stop. Do not run the full grid until you have read the verdict and said go.**

---

## (d) Full run — ONLY after PILOT: PASS and your explicit go-ahead
Separate `$200` cap (`BUDGET_FULL`), adds xAI Grok (flagship, priced
conservatively) + larger variants + a third prompt variant + a third seed.
```bash
python3 capture/probe.py --subgrid full          # probe the full model set (incl. Grok)
SUBGRID=full CONC=5 ./run_all.sh                  # ledger-gated at $200
python3 analysis/run.py --subgrid full
python3 pilot/verdict.py
```

---

### Notes
- Reset the offline dry-run any time: `PILOT_MOCK=1 ./run_all.sh` re-mints its own
  (mock) CSVs. Never resets REAL captures.
- Git: commit after each stage locally (`git add -A && git commit -m ...`). (In the
  Cowork sandbox the mounted `.git` can't unlink lock files, so commits are best
  done from your machine.)
