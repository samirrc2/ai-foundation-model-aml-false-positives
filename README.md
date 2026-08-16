# Same Transactions, Different Alarms

Computational artifact for the Discover Artificial Intelligence article:

**Same Transactions, Different Alarms: Foundation-Model Choice and AML False Positives**

### Paper summary

Large language models (LLMs) are increasingly proposed as anti-money-laundering (AML) transaction screeners, but the consequences of *which* foundation model an institution adopts have not been measured. This article runs five foundation LLMs as zero-shot AML screeners over an identical, pre-registered battery of **600 synthetic cases** (300 legitimate "hard-negative" patterns and 300 suspicious cases across eight FATF typologies), each under two prompt framings and two seeds (**12,000 model calls**), and measures how much the choice of foundation model alone changes screening outcomes on identical activity.

**Main findings:**

- On identical legitimate transactions, per-model false-positive rates span **0.3% → 83.0%** — an 82.7-percentage-point spread (95% CI [69.2, 95.3], cluster bootstrap) — and the five models differ far beyond chance (Cochran's Q = 131.6, df = 4, *P* ≈ 2×10⁻²⁷; pairwise McNemar exact, Bonferroni-corrected: all between-group comparisons significant, the two within-group comparisons not).
- The models disagree on **85.7%** of legitimate cases (95% CI [75.1, 95.4]).
- Within each provider, the false-positive rate falls monotonically as model capability (and price) rises: the cheapest models over-flag (83.0%) while their flagship siblings do not (1.0%). In the standard classification view the Matthews correlation coefficient ranges 0.96→0.31 on identical data.
- Projected to a realistic 0.1% suspicious prevalence over 1,000,000 transactions/day, model choice swings daily alert volume **~4,200 → ~830,000** (~197×), with alert precision collapsing from 20.9% to 0.12%.
- Shared blind spot: trade-based laundering is missed **18.9%** of the time (95% CI [14.0, 25.1]); structural typologies are caught near-perfectly.

This repository is the frozen dataset and deterministic analysis pipeline that regenerates those numerical results, tables, and figures, plus the Discover Artificial Intelligence manuscript package. Per-case decisions use the pre-registered modal-vote rule (decision D4): on legitimate cases a 2–2 tie is **not** counted as a false positive (strict majority required), and on suspicious cases a 2–2 tie **is** counted as caught. The rule is applied identically to every model, table, and figure.

---

## 1. Artifact Identification

| Field | Value |
|-------|-------|
| **Article title** | Same Transactions, Different Alarms: Foundation-Model Choice and AML False Positives |
| **Authors** | Samir Chincholikar, Robin Chawla |
| **Affiliations** | Independent researchers |
| **Code repository** | https://github.com/samirrc2/same-transactions-different-alarms |
| **Persistent DOI** | https://doi.org/10.24433/CO.4804007.v1 (`10.24433/CO.4804007.v1`) |
| **Contact** | Samir Chincholikar: samir.chincholikar@gmail.com; Robin Chawla: robin.chawla.cse14@iitbhu.ac.in |
| **ORCID** | Samir Chincholikar: https://orcid.org/0009-0007-2779-3492; Robin Chawla: https://orcid.org/0009-0007-2807-3948 |

### Abstract and role of the artifact

This artifact accompanies a **pre-registered** study of cross-foundation-model false-positive variance in LLM AML screening. The confirmatory experiment comprises **12,000 independent model calls** (5 models × 2 prompt variants × 2 seeds × 600 cases) using models from OpenAI and Google.

The artifact enables independent reproduction of the article's computational results. Specifically, it provides:

1. The frozen confirmatory dataset (`capsule/data/capture/runs_full_<model>_<variant>.csv`, each row carrying the model's raw response) with SHA-256 receipts (`capsule/data/frozen/`), the deterministic 600-case battery (`capsule/data/battery/full.jsonl`, content-hashed in `capsule/data/manifest/battery_manifest.json`), and the study configuration (`capsule/data/configs/`).
2. A deterministic analysis pipeline that regenerates the primary false-positive-variance endpoints with cluster-bootstrap and Wilson CIs, the standard per-model classification metrics with paired inferential tests (Cochran's Q, McNemar exact + Bonferroni), the per-typology miss rates, the prompt-sensitivity decomposition, two non-LLM baselines, and the operational alert-volume projection, into `capsule/results/`.
3. Pre-registration, its amendment and pivot, and the append-only decisions log (`capsule/docs/`).
4. The capture harness used for live collection (`capsule/code/capture/`).
5. The Discover Artificial Intelligence manuscript package (`manuscript/`).

**Default workflow (this README):** regenerate all analysis outputs from the frozen dataset. This path requires **no API keys** and incurs **no inference cost**. Re-collecting the 12,000 API calls is optional, incurs cost, and is **not required** to verify the numerical claims in the article.

---

## Code Ocean

A [Code Ocean](https://codeocean.com/) compute capsule for this artifact is available at
[https://doi.org/10.24433/CO.4804007.v1](https://doi.org/10.24433/CO.4804007.v1)
(DOI `10.24433/CO.4804007.v1`).

| Status | Detail |
|--------|--------|
| Capsule | Keys-free Reproducible Run via `/code/run` → `code/scripts/reproduce.sh` |
| Environment | `capsule/environment/Dockerfile` (Code Ocean base + pinned pip) |
| Public link / DOI | https://doi.org/10.24433/CO.4804007.v1 |
| Local reproduce | `cd capsule && bash reproduce.sh` |

The frozen dataset is committed to the repository, so the capsule reproduces every number with **no external download, no API keys, and no inference cost**.

> **Note:** this artifact adds two deterministic outputs (`classification_metrics.json`, `stats_tests.json`) beyond the original capsule. Re-run `bash reproduce.sh` and re-upload as a **new capsule version** so the persistent DOI resolves to matching output hashes.

---

## 2. Artifact Dependencies and Requirements

### Hardware

| Resource | Requirement |
|----------|-------------|
| CPU | Standard laptop or workstation (analysis is CPU-bound, single process) |
| RAM | ≥ 4 GB |
| Disk | ≥ 1 GB free (committed dataset ≈ 9 MB) |
| GPU | Not required |

### Operating system

- macOS, Linux, or Windows with WSL2
- `bash` required for `capsule/reproduce.sh` and `capsule/code/run`
- Containerized review environments (e.g., Code Ocean): Linux

### Software

| Component | Requirement |
|-----------|-------------|
| Python | ≥ 3.10 (developed on 3.12) |
| Shell | `bash` |
| Network | Not required for the default keys-free workflow |

### Software libraries

Dependencies are in `capsule/code/requirements.txt`, pinned to the tested, byte-identical environment:

- `numpy==2.2.6` — analysis (required)
- `scikit-learn==1.7.2` — rules/supervised baselines (required)
- `scipy==1.18.0` — Cochran's Q + McNemar exact P-values (required)
- `pyyaml==6.0.3` — configuration parsing (required)
- `pydantic==2.13.4` — configuration schema validation (required)
- `matplotlib` — optional, figure regeneration only
- `openai>=1.40`, `google-genai>=0.3` — optional, live re-collection only

### Input data included with the artifact

| Path | Description | Approx. size |
|------|-------------|--------------|
| `capsule/data/capture/runs_full_<model>_<variant>.csv` | Frozen confirmatory call logs (incl. raw response) — 10 files | 8.1 MB |
| `capsule/data/battery/full.jsonl`, `pilot.jsonl` | Deterministic 600-case battery (and pilot subsample) | 1.4 MB |
| `capsule/data/frozen/*.freeze.json` | Per-capture SHA-256 receipts | < 1 MB |
| `capsule/data/configs/` | Frozen battery, model, and grid configuration | < 1 MB |
| `capsule/docs/` | Pre-registration, amendment, pivot, decisions log | < 1 MB |

**Integrity (frozen confirmatory captures):** the SHA-256 of every capture CSV is recorded in its `capsule/data/frozen/*.freeze.json` receipt, and the battery hash in `capsule/data/manifest/battery_manifest.json`. The reproduction pipeline regenerates the battery from its seed and verifies the hash before analysis.

### Optional dependencies (live re-collection only)

API credentials for OpenAI and Google Gemini are required **only** for live re-collection (`capsule/code/capture/`) and are read from a local keys file. They are **not** required for the default reproduction path, which runs entirely from the committed frozen dataset.

---

## 3. Installation and Deployment

### Time estimates

| Step | Typical duration |
|------|------------------|
| Create venv + install requirements (first time) | ~1 minute |
| Default reproduction (`bash reproduce.sh`) | ~1 minute |
| Determinism check (byte-identical replication) | ~2 minutes |
| Live re-collection of 12,000 calls (optional) | hours; provider-cost |

### Installation

```bash
git clone https://github.com/samirrc2/same-transactions-different-alarms.git
cd same-transactions-different-alarms/capsule
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r code/requirements.txt
bash reproduce.sh
```

No compilation step is required. On Code Ocean, packages come from `environment/Dockerfile` — no venv step. Capsule entry is `/code/run`.

### Deployment / execution

| Goal | Command |
|------|---------|
| Verify data integrity + regenerate all results (default) | `cd capsule && bash reproduce.sh` |
| Analysis only (skip replication check) | `bash reproduce.sh --analyze-only` |
| Determinism check only (hash-compare) | `bash reproduce.sh --check-only` |
| Code Ocean entry point | `./code/run` |
| Live re-collection (optional; **not** required to verify the paper) | see `capsule/code/capture/README.md` |

Outputs are written under `capsule/results/`.

---

## 4. Reproducibility of Experiments

### Workflow

```text
capsule/data/battery/full.jsonl + capsule/data/capture/runs_full_*.csv + capsule/data/configs/
        │
        ▼
  cd capsule && bash reproduce.sh
  (→ code/src/reproduce.py: verify integrity → altrisk + classification + baselines + alertvolume
     → code/src/replication_check.py: byte-identical re-run)
        │
        ├── results/pivot_claims.json          # false-positive-variance endpoints + CIs
        ├── results/classification_metrics.json # per-model precision/recall/specificity/F1/MCC + Wilson CIs
        ├── results/stats_tests.json            # Cochran's Q + pairwise McNemar (Bonferroni) + per-typology miss
        ├── results/baselines.json              # FATF rules + supervised baselines
        ├── results/alert_volume.json           # operational projection at 0.1% prevalence
        ├── results/table1_operating_points.{csv,md}, table2_alert_volume.{csv,md}
        ├── results/metrics_summary.md          # human-readable summary
        └── results/output_hashes.json          # SHA-256 of every deterministic output
```

The primary estimand is the per-model false-positive rate on the 300 legitimate cases and the cross-model spread (max − min), cluster-bootstrapped over the eight typology strata (2,000 draws, seed 4242). All analysis is a pure, seeded function of the frozen CSVs and produces byte-identical output on every re-run (the replication check proves this).

### Expected results

After `bash reproduce.sh`, `results/` must contain the following (Table 1 / Table 2 of the article):

| Model | Provider | False-positive rate | Miss rate | Precision | Recall | Specificity | F1 | MCC |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| Gemini Flash | Google | 0.3% | 12.0% | 99.6% | 88.0% | 99.7% | 93.5% | 0.883 |
| GPT-4o | OpenAI | 1.0% | 3.3% | 99.0% | 96.7% | 99.0% | 97.8% | 0.957 |
| GPT-4.1-mini | OpenAI | 23.7% | 3.7% | 80.3% | 96.3% | 76.3% | 87.6% | 0.742 |
| Gemini Flash-Lite | Google | 24.7% | 0.7% | 80.1% | 99.3% | 75.3% | 88.7% | 0.769 |
| GPT-4o-mini | OpenAI | 83.0% | 0.0% | 54.6% | 100.0% | 17.0% | 70.7% | 0.305 |

| Quantity | Value |
|---|---|
| False-positive spread (max − min) | 82.7 pp (95% CI [69.2, 95.3]) |
| Cross-model disagreement on legitimate cases | 85.7% (95% CI [75.1, 95.4]) |
| Overall difference (Cochran's Q, df = 4) | Q = 131.6, *P* ≈ 2×10⁻²⁷ |
| Trade-based laundering miss (pooled) | 18.9% (95% CI [14.0, 25.1]) |
| Prompt-variant decision-flip rate | 7.5% (95% CI [6.9, 8.2]) |
| Projected daily alerts (1M tx/day @ 0.1%) | ~4,200 → ~830,000 (~197×) |
| Rules / supervised baseline (FP / miss) | 12.0% / 11.3%  ·  ~0% / ~0% |

The determinism check must confirm byte-identical results across two independent runs.

### Out of scope for the default workflow

- Re-issuing live model API calls (`capsule/code/capture/`)
- Any inference or API spend
- Figure regeneration (requires matplotlib; not needed to verify the numbers)

---

## 5. Other Notes

- **Pre-registration and design records:** `capsule/docs/preregistration.md`, `preregistration_pivot.md`, `preregistration_amendment.md`, `decisions_log.md`.
- **Provenance:** every capture is SHA-256-stamped in `capsule/data/frozen/*.freeze.json`; the frozen CSVs are the object of record and must not be regenerated.
- **Tie rule (pre-registered D4):** per-(model, case) decisions are the modal vote over the valid (non-ERROR) replicates. On legitimate cases a 2–2 tie is **not** counted as a false positive (strict majority required); on suspicious cases a 2–2 tie **is** counted as caught. Applied identically to every model, table, and figure.
- **Manuscript source:** the manuscript is the Springer Nature LaTeX in `manuscript/latex/` (`main.tex` + `references_discover.bib`, 43 references, `sn-basic.bst`, figures fig1–fig5), compiled to `manuscript/MANUSCRIPT_Discover_compiled.pdf` and `manuscript/MANUSCRIPT_Discover.docx` via `manuscript/latex/build_both.sh`.
- **Issues and support:** GitHub Issues, or the author emails in Section 1.

### Repository structure

```text
same-transactions-different-alarms/
├── README.md   LICENSE   CITATION.cff   .gitignore
│
├── capsule/                          # Code Ocean compute capsule (keys-free reproduce)
│   ├── reproduce.sh                  # verify integrity → analysis → replication check
│   ├── code/
│   │   ├── run                       # Code Ocean entry → scripts/reproduce.sh
│   │   ├── requirements.txt
│   │   ├── src/                      # reproduce.py, altrisk, classification, baselines,
│   │   │                             #   alertvolume, miss, stats, build_battery, …
│   │   ├── scripts/reproduce.sh
│   │   ├── capture/                  # live-collection harness (agent, orchestrator, freeze, probe)
│   │   └── tests/
│   ├── data/
│   │   ├── battery/  full.jsonl, pilot.jsonl        # frozen, hashed
│   │   ├── capture/  runs_full_*.csv (10)           # frozen confirmatory capture
│   │   ├── frozen/   *.freeze.json                  # SHA-256 receipts
│   │   └── configs/  battery.yaml, models.yaml, grid.yaml
│   ├── docs/         preregistration*.md, decisions_log.md, model_manifest.md
│   ├── environment/  Dockerfile
│   ├── metadata/     metadata.yml
│   └── results/      pivot_claims.json, classification_metrics.*, stats_tests.json,
│                     prompt_sensitivity.*, baselines.json, alert_volume.json, tables, hashes
│
└── manuscript/                       # Discover Artificial Intelligence package
    ├── MANUSCRIPT_Discover_compiled.pdf   # compiled manuscript (submission PDF)
    ├── MANUSCRIPT_Discover.docx           # Word version (same numbering, embedded figures)
    ├── COVER_LETTER.{tex,pdf,docx}        # cover letter
    ├── SUPPLEMENTARY_INFORMATION.md       # supplementary notes
    ├── figures/                           # fig1–fig5 (PDF + PNG)
    └── latex/                             # Springer Nature sn-jnl source (main.tex, .bib, .bbl, .cls, .bst) — compiles PDF + DOCX via build_both.sh
```

Generated artifacts (`.venv/`, `__pycache__/`) are gitignored. Committed analysis outputs live under `capsule/results/`.

### Reviewer quick start

```bash
git clone https://github.com/samirrc2/same-transactions-different-alarms.git
cd same-transactions-different-alarms/capsule
python3 -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
bash reproduce.sh          # ~1 min, no keys, no cost
```

Confirm `capsule/results/classification_metrics.json` and `results/pivot_claims.json` match the Expected Results tables in Section 4, and that the replication check reports byte-identical outputs.

## 6. License

MIT — see `LICENSE`.
