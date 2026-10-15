# Data (`/data`)

All inputs are **frozen and hash-verified** by the Reproducible Run. Nothing here
is fetched at run time.

```
data/
  battery/
    full.jsonl              600-case FATF/SAML-D battery (300 benign / 300 suspicious)
    pilot.jsonl             240-case stratified subsample (pilot; not used by the paper's full analysis)
  capture/
    runs_full_<model>_<variant>.csv   10 files: 5 models x {v_terse, v_fatf}
  frozen/
    full_<model>_<variant>.freeze.json  SHA-256 + row count for each capture CSV
  configs/
    models.yaml grid.yaml battery.yaml  study configuration (model registry, grid, battery spec)
  manifest/
    battery_manifest.json   battery SHA-256s, seed, per-stratum counts
```

## Battery (`battery/full.jsonl`)

Deterministically generated (seed 20260715) from FATF typologies + SAML-D/AMLSim
structure. One JSON object per case:

| field | meaning |
|---|---|
| `case_id` | unique id, e.g. `S-structuring-m-003` |
| `label` | `suspicious` or `benign` |
| `typology` | one of 8 laundering typologies (suspicious cases) or `null` |
| `benign_pattern` | legitimate pattern (benign cases) or `null` |
| `difficulty` | `easy` / `medium` / `hard` |
| `stratum` | clustering unit for the bootstrap (e.g. `suspicious:structuring`) |
| `serialized` | the raw node/edge transaction ledger shown to each model |
| `content_sha256` | hash of the serialized case |

The Reproducible Run **regenerates** this file from the seed and confirms the
SHA-256 matches `manifest/battery_manifest.json` — so the battery is provably the
one described in the preregistration.

## Capture CSVs (`capture/*.csv`)

Each row is one screening call. Columns include: `model_key`, `api_model`,
`provider`, `prompt_variant`, `seed_index`, `case_id`, `label`, `typology`,
`difficulty`, `stratum`, `prompt_hash`, `content_sha256`, `suspicious`, `decision`
(`flag` / `no_flag` / `ERROR`), `rationale`, token counts, `cost_usd`, `ok`,
`error`. Analysis uses `decision` (and `label`) only; the free-text `rationale`
and `raw_response` are retained for provenance.

Grid: 5 models × 2 prompt variants × 2 seeds × 600 cases (12,000 calls; overall
ERROR rate 0.08%). Each CSV is frozen and its SHA-256 recorded in
`frozen/full_<model>_<variant>.freeze.json`; the run verifies every one.

**Note on `runs_full_openai_4o_mini_v_terse.csv`.** This file has more than 1,200
rows because collection was resumed after a provider daily-rate-limit interruption;
the append-only log therefore contains a small number of superseded rows. The
analysis reduces to one decision per (seed, case) by modal vote and never
double-counts, and the freeze receipt hashes the exact shipped file — so the result
is unaffected and fully reproducible.

## Provenance / collection

The CSVs were produced by the harness in `code/capture/` against live OpenAI and
Google APIs (see `docs/data_collection.md`). That step is **not** part of this
capsule's Reproducible Run.
