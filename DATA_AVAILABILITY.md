# Data availability

All data required to reproduce every result in the article are included in this repository and are released under MIT. The study uses only **synthetic** transaction data — no human participants, no proprietary records, and no live model access are needed to reproduce any reported number.

## Frozen inputs (pre-registered)

- `capsule/data/battery/full.jsonl` — the deterministic 600-case FATF/SAML-D-anchored battery (300 legitimate hard-negatives + 300 suspicious across eight typologies); `pilot.jsonl` is the seeded stratified subsample.
- `capsule/data/configs/battery.yaml`, `models.yaml`, `grid.yaml` — the battery specification, model registry, and capture grid.
- `capsule/data/manifest/battery_manifest.json` — content hash of the battery; the reproduction pipeline regenerates the battery from seed 20260715 and verifies this hash before analysis.
- `capsule/docs/preregistration.md`, `preregistration_pivot.md`, `preregistration_amendment.md`, `decisions_log.md` — the frozen design contract and its amendment/pivot history.

## Frozen response corpus (the elicitations)

- `capsule/data/capture/runs_full_<model>_<variant>.csv` — the **12,000-call** confirmatory capture (5 models × 2 prompt variants × 2 seeds × 600 cases), each row carrying the model's raw JSON response, served-model fingerprint, token counts, and per-call cost. Ten files.
- `capsule/data/frozen/*.freeze.json` — per-capture SHA-256 receipts; the analysis refuses to run on any CSV whose hash does not match its receipt.

## Integrity

- Every capture CSV is SHA-256-stamped in its `capsule/data/frozen/*.freeze.json` receipt; the battery hash is fixed in `capsule/data/manifest/battery_manifest.json`.
- Verified: `cd capsule && bash reproduce.sh` regenerates every file under `capsule/results/` **byte-for-byte**, offline, with no API keys and no inference cost. The determinism check (`code/src/replication_check.py`) re-runs the analysis in a second output directory and confirms identical SHA-256 for every result file.

## Reproducibility — the chain (journal-facing)

**Frozen corpus → results (the reproduction of record).** `bash reproduce.sh` regenerates `results/pivot_claims.json` (false-positive-variance endpoints + CIs), `results/classification_metrics.json` (per-model precision/recall/specificity/F1/MCC + Wilson CIs), `results/stats_tests.json` (Cochran's Q + pairwise McNemar, Bonferroni), `results/baselines.json`, `results/alert_volume.json`, and the manuscript tables — all deterministically from the frozen battery and capture CSVs. Output hashes are recorded in `results/output_hashes.json`.

**On "re-collecting" the LLM responses.** LLM outputs are non-deterministic and provider models are updated and retired over time — indeed, one selected snapshot was deprecated mid-study, which the article reports as an instance of the substitution effect it analyses. Re-querying the models would therefore not reproduce the same corpus and is neither expected nor meaningful for reproducibility. The frozen response corpus is the primary data; `capsule/code/capture/` is included only to document how it was collected (requires provider API keys; not needed to reproduce any result).

## Machine-readable claims

Every quantitative claim in the article, with its confidence interval and the configuration hash that produced it, is emitted to `capsule/results/pivot_claims.json`, `classification_metrics.json`, and `stats_tests.json`.

## Persistent identifiers

- GitHub repository: https://github.com/samirrc2/same-transactions-different-alarms
- Code Ocean compute capsule (persistent DOI): https://doi.org/10.24433/CO.4804007.v1
