# ARCHITECTURE — P4

## The wall

```
        ┌───────────────────────────┐        ┌────────────────────────────┐
        │   CAPTURE  (perishable)   │        │   ANALYSIS  (reproducible) │
        │   impure · costs money    │  ───▶  │   pure · $0 · byte-stable  │
        │   live vendor APIs        │ frozen │   reads FROZEN csv only    │
        │   resumable · quota-aware │  csv   │   seeded · deterministic   │
        └───────────────────────────┘        └────────────────────────────┘
```

No analysis module issues a network call or reads an unfrozen CSV. Capture writes
append-only raw CSVs and a freeze receipt (SHA-256); analysis consumes only frozen
CSVs and emits `claims.json`. Re-running analysis on the same frozen inputs is
byte-identical.

## The atom: a *screening cell*

```
screening cell = (model_key, prompt_variant, seed_index, case_id)
              →  one constrained-JSON AML screening call
              →  {"suspicious": bool, "typology": str|null, "rationale": str}
              →  flag | no_flag | ERROR   (+ provenance: prompt_hash, seed,
                                            retrieved_at, content SHA-256)
```

The battery of cases is minted once, offline, deterministically, and frozen
(hashed). Each model screens every case under every (variant, seed).

## Data flow

```
config/battery.yaml ─┐
config/grid.yaml   ──┼─▶ capture/build_battery.py ─▶ data/battery/*.jsonl (+ manifest, SHA-256)
config/models.yaml ──┘                                     │
                                                           ▼
config/{models,grid}.yaml ─▶ capture/orchestrator.py ─▶ data/raw/runs_<model>_<variant>.csv
   (agent.py provider router; ledger.py priced spend gate; PILOT_MOCK swaps a fake screener)
                                                           │  capture/freeze.py
                                                           ▼
                                              data/frozen/<...>.freeze.json (SHA-256, read-only CSV)
                                                           │
analysis/{miss,correlation,defense,stats}.py ─▶ analysis/run.py ─▶ claims.json
                                                           │
                                              pilot/verdict.py ─▶ pilot/PILOT_VERDICT.md
```

## Modules

**capture/**
- `secrets.py` — loads `../API Keys/keys.env.txt`; provider→key with numbered-key
  pool + round-robin/failover on 429/quota; env wins over file.
- `probe.py` — one 1-token live call per pilot model → served-model fingerprint +
  measured per-call price → `manifest/probe_receipts.json`. Refuses to proceed if
  a model is unreachable.
- `build_battery.py` — deterministic offline battery generator (FATF/SAML-D/AMLSim
  typologies), stratified, hashed, frozen. **$0.**
- `agent.py` — OpenAI-compatible provider router (base_url per family: OpenAI,
  xAI, Gemini). Builds the supervisory screening prompt, calls one model, parses
  strict JSON → `flag/no_flag/ERROR`. Contains the deterministic `PILOT_MOCK`
  fake screener.
- `ledger.py` — per-model `{calls,in_tok,out_tok,usd}`; prices every call;
  persists every N; **HARD abort** the instant projected-or-actual cumulative
  spend crosses the active cap; worst-case reservation makes the cap safe under
  concurrency.
- `orchestrator.py` — condition-driven bounded worker pool; API call OUTSIDE the
  lock, ledger mutation + append INSIDE the lock; resumable (append-only, keyed by
  (model,variant,seed,case); completed cells skipped and never re-billed);
  freeze+hash on landing.

**analysis/** (pure, $0)
- `miss.py` — per-cell miss (false-negative) determination vs ground truth;
  modal-per-(model,case) reduction; ERROR/NA handling.
- `correlation.py` — marginal miss rates; independence-predicted joint-miss;
  observed joint-miss; ratio; pairwise Cohen κ / Scott π / Gwet AC1 matrices;
  systemic-failure ratio; within- vs cross-family contrast; prevalence/churn.
- `defense.py` — defense-in-depth recovery rate for (primary, heterogeneous
  second-line) pairs; residual joint miss vs the independence-promised reduction.
- `stats.py` — cluster bootstrap over **typologies** (seeded), 95% CIs on every
  headline; Wilson CIs for proportions.
- `run.py` — SINGLE ENTRYPOINT → `claims.json` (every cited number + its CI + the
  config/battery hash that produced it).

**config/**
- `schema.py` — one pydantic-v2 config schema; the atom is a screening cell.
- `models.yaml` — registry (pilot cheap subset + full set; prices; snapshot
  strings; probe-receipt slots; `pilot: true|false`).
- `battery.yaml` — typology battery spec (FATF/SAML-D/AMLSim mapping, labels,
  sizes, seeds).
- `grid.yaml` — K models × seeds × prompt variants; pilot vs full subgrids;
  budgets; rpm limits; retries.
- `loader.py` — resolves configs into screening conditions and subgrids.

**pilot/** — pilot outputs, `PILOT_RESULTS.md`, `PILOT_VERDICT.md`.
**manifest/** — config hash, model fingerprints, seeds, spend totals.
**run_all.sh** — `./run_all.sh` with `SUBGRID=pilot|full`, `PILOT_MOCK=1`, `CONC=`.

## Invariants
- ERROR is first-class; never coerced to flag/miss.
- Runs are append-only; captures are frozen+hashed on landing; frozen CSVs are
  read-only.
- Spend cap is hard, pre-reserved under concurrency, and pre-flight-checked.
- Analysis is a pure function of frozen inputs + seeds.
- Dual-use: measure misses; never optimize evasion (no arm searches for
  screener-beating text).
