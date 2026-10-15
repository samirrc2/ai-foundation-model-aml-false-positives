# Data-collection harness (reference only — NOT run by the capsule)

These modules produced the frozen capture CSVs in `data/capture/`. They call live
OpenAI and Google APIs, require API keys, and spend money — so they are **not part
of the Reproducible Run** and are included solely for transparency and audit.

- `orchestrator.py` — condition-driven, resumable, ledger-gated capture; one CSV per
  (model, prompt variant); freezes + hashes on landing; parallel per-provider streams.
- `agent.py` — provider router (OpenAI / xAI OpenAI-compatible / Gemini) + strict
  constrained-JSON parse; also the deterministic offline mock used for pipeline tests.
- `ledger.py` — priced per-model spend ledger with a hard budget cap.
- `secrets.py` — loads API keys from a local keys file (never committed).
- `freeze.py` — writes the SHA-256 freeze receipts in `data/frozen/`.
- `probe.py` / `check_limits.py` — pre-flight model/limit probes.

The analysis in `code/src/` reads only the frozen outputs; it never imports these
modules. See `docs/data_collection.md` for methodology.
