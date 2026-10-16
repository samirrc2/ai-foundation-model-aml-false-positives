# AI foundation model choice and false positive variation in Anti Money Laundering transaction screening

Computational artifact for the Discover Artificial Intelligence article:

**AI foundation model choice and false positive variation in Anti Money Laundering transaction screening**

---

## 📄 Start here: Reproducibility Documentation

### ➡️ [Supporting Data and Code — Reproducibility Documentation (PDF)](REPRODUCIBILITY_DOCUMENTATION.pdf)

This is the complete guide to the repository — **read it first.** It explains, section by section, *what this repository contains and how to use it*: every data input and its schema, every analysis script (what it consumes and what it produces), all generated outputs, how the data were collected, and the single-command offline reproduction and byte-identical verification. Anyone reviewing, reproducing, or reusing the artifact should begin there.

---

### Paper summary

Large language models (LLMs) are increasingly proposed as anti-money-laundering (AML) transaction screeners, but the consequences of *which* foundation model an institution adopts have not been measured. This article runs five foundation LLMs as zero-shot AML screeners over an identical, pre-registered battery of **600 synthetic cases** (300 legitimate "hard-negative" patterns and 300 suspicious cases across eight FATF typologies), each under two prompt framings and two seeds (**12,000 model calls**), and measures how much the choice of foundation model alone changes screening outcomes on identical activity.

**Main findings:**

- On identical legitimate transactions, per-model false-positive rates span **2.3% → 85.7%** — an 83.3-percentage-point spread (95% CI [71.8, 93.7], cluster bootstrap) — and the five models differ far beyond chance (Cochran's Q = 585.0, df = 4, *P* ≈ 2.7×10⁻¹²⁵; pairwise McNemar exact, Bonferroni-corrected: 9 of the 10 comparisons significant).
- The models disagree on **88.7%** of legitimate cases (95% CI [82.2, 95.0]).
- Within each provider, the false-positive rate falls monotonically as model tier rises: the lower-tier models over-flag (85.7%) while their flagship siblings do not (7.7%). In the standard classification view the Matthews correlation coefficient ranges 0.89→0.28 on identical data.
- Projected to a realistic 0.1% suspicious prevalence over 1,000,000 transactions/day, model choice swings daily alert volume **~24,190 → ~856,810** (~35×), with alert precision collapsing from 3.6% to 0.12%. Across the four deployable single-call configurations the ratio runs 36- to 196-fold.
- Shared blind spot: trade-based laundering is missed **18.9%** of the time (95% CI [14.0, 25.1]); structural typologies are caught near-perfectly.

This repository is the frozen dataset and deterministic analysis pipeline that regenerates those numerical results, tables, and figures, plus the Discover Artificial Intelligence manuscript package. Per-case decisions use the pre-registered modal-vote rule (decision D4): the modal replicate decision with a 2–2 tie resolved toward **flag** on both labels, independently of the case label. The submitted analysis deviated from D4 on legitimate cases by requiring a strict majority; that deviation is corrected here and retained in Table 1 as the as-submitted row. The rule is applied identically to every model, table, and figure.

---

## 1. Artifact Identification

| Field | Value |
|-------|-------|
| **Article title** | AI foundation model choice and false positive variation in Anti Money Laundering transaction screening |
| **Authors** | Samir Chincholikar, Robin Chawla |
| **Affiliations** | Independent researchers |
| **Code repository** | https://github.com/samirrc2/ai-foundation-model-aml-false-positives |
| **Persistent DOI** | [10.5281/zenodo.23424852](https://doi.org/10.5281/zenodo.23424852) (concept DOI, resolves to the latest version) |
| **Contact** | Samir Chincholikar: samir.chincholikar@gmail.com; Robin Chawla: robin.chawla.cse14@iitbhu.ac.in |
| **ORCID** | Samir Chincholikar: https://orcid.org/0009-0007-2779-3492; Robin Chawla: https://orcid.org/0009-0007-2807-3948 |

### Abstract and role of the artifact

This artifact accompanies a **pre-registered** study of cross-foundation-model false-positive variance in LLM AML screening. The confirmatory experiment comprises **12,000 independent model calls** (5 models × 2 prompt variants × 2 seeds × 600 cases) using models from OpenAI and Google.

The artifact enables independent reproduction of the article's computational results. Specifically, it provides:

1. The frozen confirmatory dataset (`data/capture/runs_full_<model>_<variant>.csv`, each row carrying the model's raw response) with SHA-256 receipts (`data/frozen/`), the deterministic 600-case battery (`data/battery/full.jsonl`, content-hashed in `data/manifest/battery_manifest.json`), and the study configuration (`data/configs/`).
2. A deterministic analysis pipeline that regenerates the primary false-positive-variance endpoints with cluster-bootstrap and Wilson CIs, the standard per-model classification metrics with paired inferential tests (Cochran's Q, McNemar exact + Bonferroni), the per-typology miss rates, the prompt-sensitivity decomposition, two non-LLM baselines, and the operational alert-volume projection, into `results/`.
3. Pre-registration, its amendment and pivot, and the append-only decisions log (`docs/`).
4. The capture harness used for live collection (`capture/`).
5. The Discover Artificial Intelligence manuscript package (`paper/`).

**Default workflow (this README):** regenerate all analysis outputs from the frozen dataset. This path requires **no API keys** and incurs **no inference cost**. Re-collecting the 12,000 API calls is optional, incurs cost, and is **not required** to verify the numerical claims in the article.

---

## Zenodo

This artifact is archived on Zenodo as a plain source release, under the concept DOI
[10.5281/zenodo.23424852](https://doi.org/10.5281/zenodo.23424852), which always resolves to the most recent version. There is no container image and
no compute capsule: the repository is flat, and everything reproduces from the frozen data with
a single command.

| | |
|---|---|
| Reproduce | `bash reproduce.sh` from the repository root |
| Environment | `requirements.txt` (pinned); `environment/Dockerfile` is optional |
| Verify | `bash build/build_all.sh` rebuilds every deliverable and runs every gate |
| Tests | `pytest tests -q` |

The frozen dataset is committed, so every number reproduces with **no external download, no API
keys and no inference cost**. Two independent runs are byte-identical.

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
- `bash` required for `reproduce.sh` and `reproduce.sh`
- Containerized review environments (e.g. a container): Linux

### Software

| Component | Requirement |
|-----------|-------------|
| Python | ≥ 3.10 (developed on 3.12) |
| Shell | `bash` |
| Network | Not required for the default keys-free workflow |

### Software libraries

The pinned analysis environment is `requirements.txt`:

- `numpy==2.2.6` — analysis (required)
- `scikit-learn==1.7.2` — rules/supervised baselines (required)
- `scipy==1.18.0` — Cochran's Q + McNemar exact P-values (required)
- `pyyaml==6.0.3` — configuration parsing (required)
- `pydantic==2.13.4` — configuration schema validation (required)
- `pytest==8.3.5` — optional, `tests/` sanity checks

Not part of the pinned analysis environment (so **not** in `requirements.txt`): `matplotlib`, needed only if you choose to regenerate the static figures, and the `openai` / `google-genai` SDKs, needed only for optional live re-collection under `capture/`. Neither is required to reproduce any reported number.

### Input data included with the artifact

| Path | Description | Approx. size |
|------|-------------|--------------|
| `data/capture/runs_full_<model>_<variant>.csv` | Frozen confirmatory call logs (incl. raw response) — 10 files | 8.1 MB |
| `data/battery/full.jsonl`, `pilot.jsonl` | Deterministic 600-case battery (and pilot subsample) | 1.4 MB |
| `data/frozen/*.freeze.json` | Per-capture SHA-256 receipts | < 1 MB |
| `data/configs/` | Frozen battery, model, and grid configuration | < 1 MB |
| `docs/` | Pre-registration, amendment, pivot, decisions log | < 1 MB |

**Integrity (frozen confirmatory captures):** the SHA-256 of every capture CSV is recorded in its `data/frozen/*.freeze.json` receipt, and the battery hash in `data/manifest/battery_manifest.json`. The reproduction pipeline regenerates the battery from its seed and verifies the hash before analysis.

### Optional dependencies (live re-collection only)

API credentials for OpenAI and Google Gemini are required **only** for live re-collection (`capture/`) and are read from a local keys file. They are **not** required for the default reproduction path, which runs entirely from the committed frozen dataset.

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
git clone https://github.com/samirrc2/ai-foundation-model-aml-false-positives.git
cd ai-foundation-model-aml-false-positives
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
bash reproduce.sh
```

No compilation step is required. Install the pinned dependencies with `pip install -r requirements.txt`, or build `environment/Dockerfile` if you prefer a container. The entry point is `bash reproduce.sh`.

### Deployment / execution

| Goal | Command |
|------|---------|
| Verify data integrity + regenerate all results (default) | `bash reproduce.sh` |
| Analysis only (skip replication check) | `bash reproduce.sh --analyze-only` |
| Determinism check only (hash-compare) | `bash reproduce.sh --check-only` |
| Entry point | `bash reproduce.sh` |
| Live re-collection (optional; **not** required to verify the paper) | see `capture/README.md` |

Outputs are written under `results/`.

---

## 4. Reproducibility of Experiments

### Workflow

```text
data/battery/full.jsonl + data/capture/runs_full_*.csv + data/configs/
        │
        ▼
  bash reproduce.sh
  (→ analysis/reproduce.py: verify integrity → altrisk + classification + correlated_miss
     + baselines + alertvolume + aggregation_sensitivity + figures
     → analysis/replication_check.py: byte-identical re-run)
        │
        ├── results/pivot_claims.json          # false-positive-variance endpoints + CIs
        ├── results/classification_metrics.json # per-model precision/recall/specificity/F1/MCC + Wilson CIs
        ├── results/stats_tests.json            # Cochran's Q + pairwise McNemar (Bonferroni) + per-typology miss
        ├── results/correlated_miss.json        # Cohen's kappa / Scott's pi / Gwet's AC1 on the miss outcome
        ├── results/aggregation_sensitivity.json # every aggregation policy + single-call configuration
        ├── results/prompt_sensitivity.{json,csv} # per-model FP under each prompt variant
        ├── results/baselines.json              # FATF rules + supervised baselines
        ├── results/alert_volume.json           # operational projection at 0.1% prevalence
        ├── results/table5_aggregation_sensitivity.csv # the nine-row aggregation table
        ├── results/table1_operating_points.{csv,md}, table2_alert_volume.{csv,md}
        ├── results/metrics_summary.md          # human-readable summary
        └── results/output_hashes.json          # SHA-256 of every deterministic output
```

The primary estimand is the per-model false-positive rate on the 300 legitimate cases and the cross-model spread (max − min), cluster-bootstrapped over the eight case-template strata (2,000 draws, seed 4242). All analysis is a pure, seeded function of the frozen CSVs and produces byte-identical output on every re-run (the replication check proves this).

### Expected results

After `bash reproduce.sh`, `results/` must contain the following (Table 1 / Table 2 of the article):

| Model | Provider | False-positive rate | Miss rate | Precision | Recall | Specificity | F1 | MCC |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| Gemini Flash | Google | 2.3% | 12.0% | 97.4% | 88.0% | 97.7% | 92.5% | 0.861 |
| GPT-4o | OpenAI | 7.7% | 3.3% | 92.7% | 96.7% | 92.3% | 94.6% | 0.891 |
| GPT-4.1-mini | OpenAI | 37.0% | 3.7% | 72.3% | 96.3% | 63.0% | 82.6% | 0.629 |
| Gemini Flash-Lite | Google | 44.0% | 0.7% | 69.3% | 99.3% | 56.0% | 81.6% | 0.614 |
| GPT-4o-mini | OpenAI | 85.7% | 0.0% | 53.9% | 100.0% | 14.3% | 70.0% | 0.278 |

| Quantity | Value |
|---|---|
| False-positive spread (max − min) | 83.3 pp (95% CI [71.8, 93.7]) |
| Cross-model disagreement on legitimate cases | 88.7% (95% CI [82.2, 95.0]) |
| Overall difference (Cochran's Q, df = 4) | Q = 585.0, *P* ≈ 2.7×10⁻¹²⁵ |
| Trade-based laundering miss (pooled) | 18.9% (95% CI [14.0, 25.1]) |
| Prompt-variant decision-flip rate | 7.5% (95% CI [6.9, 8.2]) |
| Projected daily alerts (1M tx/day @ 0.1%) | ~24,190 → ~856,810 (~35×) |
| Rules / supervised baseline (FP / miss) | 12.0% / 11.3%  ·  ~0% / ~0% |

The determinism check must confirm byte-identical results across two independent runs.

### Out of scope for the default workflow

- Re-issuing live model API calls (`capture/`)
- Any inference or API spend

---

## 5. Other Notes

- **Pre-registration and design records:** `docs/preregistration.md`, `preregistration_pivot.md`, `preregistration_amendment.md`, `decisions_log.md`.
- **Provenance:** every capture is SHA-256-stamped in `data/frozen/*.freeze.json`; the frozen CSVs are the object of record and must not be regenerated.
- **Tie rule (pre-registered D4):** per-(model, case) decisions are the modal vote over the valid (non-ERROR) replicates. On legitimate cases a 2–2 tie is **not** counted as a false positive (strict majority required); on suspicious cases a 2–2 tie **is** counted as caught. Applied identically to every model, table, and figure.
- **Manuscript source:** the manuscript is the Springer Nature LaTeX in `paper/` (`paper/manuscript_full.tex` + `paper/references_discover.bib`, 44 cited references, `paper/sn-jnl.cls` and `paper/sn-basic.bst`, figures fig1–fig6), compiled to `paper/manuscript_full.pdf` and `paper/manuscript_full.docx` via `build/build_all.sh`, which also runs every gate.
- **Issues and support:** GitHub Issues, or the author emails in Section 1.

### Repository structure

```text
ai-foundation-model-aml-false-positives/
├── README.md   LICENSE   CITATION.cff   .gitignore
│
├── paper/                            # manuscript, figures and build inputs
│   ├── manuscript_full.{tex,pdf,docx} # manuscript and its Word companion
│   ├── manuscript_full_tracked.{pdf,docx} # marked copy: additions yellow, deletions struck red
│   ├── cover_letter.{tex,pdf,docx}
│   └── fig*.{pdf,png}, sn-jnl.cls, references_discover.bib
├── analysis/                         # the analysis pipeline
├── capture/                          # live-collection harness (not run to reproduce)
├── build/                            # build scripts and eleven gates, run by build_all.sh
│                                     #   check_results_fresh, check_journal_requirements,
│                                     #   check_binding, check_coverage, check_table_agg,
│                                     #   check_readme, check_marked, check_tracked_docx,
│                                     #   check_verbatim, check_docx_citations, check_docx_parity
├── config, data/, docs/, results/, tests/
├── reproduce.sh                      # one command, offline, no keys
├── requirements.txt, environment/Dockerfile
└── README.md, LICENSE, CITATION.cff, .zenodo.json, REPRODUCIBILITY_DOCUMENTATION.pdf
```

Generated artifacts (`.venv/`, `__pycache__/`) are gitignored. Committed analysis outputs live under `results/`.

### Quick start

```bash
git clone https://github.com/samirrc2/ai-foundation-model-aml-false-positives.git
cd ai-foundation-model-aml-false-positives
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash reproduce.sh          # ~1 min, no keys, no cost
```

`results/classification_metrics.json` and `results/pivot_claims.json` should match the Expected Results tables above, and the replication check should report byte-identical outputs.

## 6. License

MIT — see `LICENSE`.
