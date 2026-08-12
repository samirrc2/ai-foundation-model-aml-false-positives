# Same Transactions, Different Alarms

Foundation-Model Choice as an Ungoverned Driver of False-Positive Burden in LLM
Anti-Money-Laundering Screening.

This repository holds the complete submission for the paper and its one-click
reproducibility capsule, in a single place.

## Layout

| Path | Contents |
|---|---|
| [`manuscript/`](manuscript/) | *Scientific Reports* submission package — compiled PDF, Springer Nature LaTeX source, figures, cover letter, supplementary information, compliance checklist, and file-by-file audit. |
| [`capsule/`](capsule/) | Code Ocean reproducibility capsule — frozen data, analysis code, Docker environment, and results. Running `capsule/reproduce.sh` (or the Code Ocean **Reproducible Run**) verifies data integrity, recomputes every reported number, and confirms the outputs are byte-identical across two independent runs, offline and at zero cost. |

## Reproduce the paper

```bash
cd capsule
bash reproduce.sh
```

See [`capsule/README.md`](capsule/README.md) for details and
[`capsule/AUDIT.md`](capsule/AUDIT.md) for the integrity/replication record.

## Manuscript

The submission PDF is
[`manuscript/MANUSCRIPT_ScientificReports_compiled.pdf`](manuscript/MANUSCRIPT_ScientificReports_compiled.pdf).
To rebuild it from source, see [`manuscript/latex/README.md`](manuscript/latex/README.md).

## Authors

Samir Chincholikar (first author); Robin Chawla (corresponding author). Independent
Researchers. No competing interests. Synthetic data only.
