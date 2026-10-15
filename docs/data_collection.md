# Data collection (not part of the Reproducible Run)

The frozen capture CSVs in `data/capture/` were produced once, against live vendor
APIs, by the harness in `code/capture/`. This step requires API keys, spends money,
and is intentionally **excluded** from the capsule's Reproducible Run. It is
documented here and the source is included for full transparency.

## Design (CAPTURE ↔ ANALYSIS wall)

- **CAPTURE** (perishable): talks to live OpenAI and Google APIs, is resumable and
  quota-aware, prices every call against a hard budget ledger, and freezes +
  SHA-256-hashes each output CSV the moment it lands.
- **ANALYSIS** (this capsule): reads only the frozen CSVs, is pure and seeded, and
  is byte-identical on re-run.

No analysis step issues a network call; no capture output is edited after freezing.

## Grid

- **Models (5):** GPT-4o-mini, GPT-4.1-mini, GPT-4o (OpenAI); Gemini Flash,
  Gemini Flash-Lite (Google). Exact served snapshots recorded per row
  (`api_model`) and in `docs/model_manifest.md`.
- **Conditions:** 2 supervisory prompt variants (`v_terse`, `v_fatf`) × 2 seeds ×
  600 cases = 12,000 calls. Temperature 0. Constrained-JSON output
  `{suspicious, typology, rationale}`.
- **Cost:** ~US$8 total. Overall ERROR rate 0.08%.

## Reproducing the collection (optional, live, costs money)

Not required to reproduce the paper. With OpenAI + Google API keys configured, the
harness in `code/capture/` (orchestrator, agent, ledger, freeze) re-collects the
grid; see the paper's working repository for the full runner. Because vendor models
are updated and deprecated over time (e.g., Google deprecated the Gemini 2.0 Flash
snapshots on 1 June 2026, mid-study), a fresh collection cannot be byte-identical to
the frozen data — which is precisely the model-substitution instability the paper
documents. The authoritative record is therefore the frozen, hash-verified CSVs
shipped in `data/capture/`.

## Why analysis, not collection, is the reproducible artifact

Reproducibility here means: *given the frozen model responses, every number in the
paper follows deterministically.* The Reproducible Run proves that end to end
(regenerates and hash-checks the battery; hash-checks every capture CSV; recomputes
all estimands; and confirms byte-identical outputs across two runs). Re-querying
the vendors is a different, non-reproducible activity by nature.
