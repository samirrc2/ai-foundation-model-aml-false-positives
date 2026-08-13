# Capsule audit — Same Transactions, Different Alarms

Independent verification performed on the assembled capsule. All checks pass.

## 1. Reproducible Run (`code/run`)
- **Data integrity: PASS** — battery regenerated from seed 20260715; SHA-256 matches
  the shipped `data/battery/full.jsonl` **and** `data/manifest/battery_manifest.json`.
  All **10/10** capture CSVs match their freeze-receipt SHA-256.
- **Byte-identical re-run: PASS** — the full analysis run twice into isolated output
  directories produces identical SHA-256 for every result file
  (`pivot_claims.json`, `baselines.json`, `alert_volume.json`, both table CSVs,
  `metrics_summary.md`).
- **Verdict: REPRODUCIBLE** (see `results/replication_check.md`).

## 2. Results match the manuscript
| Quantity | Reproduced |
|---|---|
| FP spread (max−min) | 82.7 pp (CI 69.2–95.3) |
| Cross-model disagreement (benign) | 85.7% (CI 75.1–95.4) |
| Per-model FP | 0.3 / 1.0 / 23.7 / 24.7 / 83.0 % |
| Overall FP difference — Cochran's Q (df=4) | Q = 131.55, P ≈ 2×10⁻²⁷ |
| Trade-based miss | 18.9% (CI 14.0–25.1) |
| Prompt flip | 7.5% (CI 6.9–8.2) |
| Rules / supervised baseline FP | 12.0% / 0.0% |
| Alert volume @0.1% (1M/day) | ~4,210 → ~830,170 |

`pivot_claims.json` carries `meta.status = CONFIRMATORY` (pre-registered full run;
the estimands and the modal-vote tie rule were fixed in advance — see
`docs/preregistration.md` and `docs/decisions_log.md`).

## 3. Tests
`pytest code/tests` → **2 passed** (headline numbers + data integrity; byte-identical re-run).

## 4. Security / hygiene
- **No secrets** anywhere: scan across `.py/.json/.md/.yaml/.txt/.csv` for OpenAI,
  Google, xAI key patterns and PEM blocks returns nothing. `code/capture/secrets.py`
  contains no hardcoded keys (it only reads a local, uncommitted keys file).
- No `.env` / `keys.env` committed; `.gitignore` blocks them.

## 5. Environment
- `environment/Dockerfile` pins numpy 2.2.6, scikit-learn 1.7.2, scipy 1.15.2,
  pyyaml 6.0.3, pydantic 2.13.4 (and pytest 8.3.5 for the optional tests) on a Code
  Ocean base image; matches `code/requirements.txt`. scipy backs the Cochran's Q and
  McNemar exact P-values in `classification.py`.
- Analysis uses only these + the Python standard library. No network, no API keys,
  no cost. The data-collection SDKs (openai, google-genai) are **not** installed in
  the Reproducible Run environment — capture is out of scope for this capsule.

## 6. Known housekeeping (harmless)
- `code/**/__pycache__/` and `code/.pytest_cache/` are present from local execution
  and are **git-ignored** (excluded from a git-based Code Ocean export). Delete them
  before a raw zip export if desired.
- `docs/battery_manifest.json` and `docs/probe_receipts.json` are provenance copies;
  the authoritative served-model list is `docs/model_manifest.md`.

## How to re-verify
```bash
bash reproduce.sh          # -> results/replication_check.md : REPRODUCIBLE
pytest code/tests -q       # -> 2 passed
```
