# P4 — Novelty sweep provenance (live)

**Swept:** 2026-07-15 · **Mode:** web-search live sweep (literature-index APIs
[OpenAlex / Semantic Scholar / arXiv / Crossref] unreachable from this
environment; adjudication done in-line rather than via the Stage-4 Claude judge).
This file stands in for `sweep.json` until a full index-backed sweep is run.

## Adjudicated candidates

| # | Paper (id) | Vector that surfaced it | Label | Conf | One-line justification |
|---|------------|-------------------------|-------|------|------------------------|
| 1 | Correlated Errors in Large Language Models (arXiv 2506.07962, ICML'25; Kim, Peng, N. Garg) | cross-model error correlation | **TEMPLATE_VISIBLE** | 0.75 | Exact formalism — cross-model error correlation over 350+ models, shared architecture/provider drives correlation — but hiring + LLM-judge domains, no AML/screening object. Scoop template. |
| 2 | Algorithmic Monocultures in Hiring (arXiv 2605.27371; Bommasani, Bana, Creel, Jurafsky, Liang) | algorithmic monoculture correlated rejection | **TEMPLATE_VISIBLE** | 0.70 | Individual+group homogeneity of rejections on 3M applicants; monoculture formalism, hiring domain. Template, not AML. |
| 3 | Representation Homogeneity & Systemic Instability in AI-Dominated Financial Markets (arXiv 2604.22818) | foundation-model monoculture systemic risk | ADJACENT | 0.65 | Structural homogeneity -> instability in trading/markets; different object (market signals, not screening misses). |
| 4 | Model Monoculture Risk: Systemic AI Convergence in Banking & Financial Markets (Preprints 202603.0393) | monoculture banking systemic | ADJACENT | 0.60 | Conceptual banking/markets monoculture; no measurement of screening-miss correlation. |
| 5 | The Oracle's Fingerprint: Correlated AI Forecasting Errors (arXiv 2605.00844) | correlated AI errors bias transmission | ADJACENT | 0.60 | Correlated forecasting errors + bias-transmission limits; forecasting task, not AML detection. |
| 6 | AI and Systemic Risk / algorithmic herding (arXiv 2604.03272) | systemic risk herding foundation models | ADJACENT | 0.55 | Performative prediction + herding in markets; macro-market object. |
| 7 | Algorithmic Monoculture and its Critics (arXiv 2604.06047) | monoculture critique | ADJACENT | 0.50 | Theory/critique of the monoculture construct; no domain measurement. |
| 8 | Risk Analysis for Governed LLM Multi-Agent Systems (arXiv 2508.05687) | agent monoculture correlated failure | ADJACENT | 0.55 | Agentic-governance framing of monoculture blind spots; no AML miss-correlation estimand. |
| 9 | Explainable AML Triage with LLMs (arXiv 2604.19755) | LLM AML triage | ADJACENT | 0.55 | AML + LLM, but evidence-retrieval/triage capability (B1/B2), not reliability/correlation. |
| 10 | Tabular CCFD adversarial transferability (arXiv 2508.14699) | fraud detection correlated misses | ADJACENT | 0.50 | Gradient/tabular adversarial transfer in classical ML; different attack surface. |
| 11 | In-Context Learning for Money Laundering Detection in Financial Graphs (arXiv 2507.14785) | in-context AML graphs | **FOUNDATION** | 0.70 | Graph-serialization LLM-AML precedent to stand on (method + citable format). |
| 12 | Kleinberg & Raghavan, PNAS 2021 | monoculture correlated failure | **FOUNDATION** | 0.90 | Supplies the monoculture -> correlated-failure mechanism and null. |
| 13 | Bommasani et al., NeurIPS 2022 (homogenization) | systemic-failure ratio | **FOUNDATION** | 0.85 | Homogenization metrics: systemic-failure ratio vs independence — the estimator scaffold. |

## Novelty verdict

**CLEAR** — no DIRECT_HIT. No prior work measures cross-MODEL AML/sanctions
screening-miss correlation with a joint-miss-vs-independence estimand or a
defense-in-depth recovery quantification. Two strong TEMPLATE_VISIBLE hits
(2506.07962, 2605.27371) confirm the monoculture template is marching
domain-by-domain (hiring landed May 2026) and put **scoop risk HIGH**.

## Human-review queue (routing: DIRECT_HIT any conf, or TEMPLATE_VISIBLE conf >= 0.7)

- arXiv 2506.07962 — Correlated Errors in Large Language Models (ICML'25) — conf 0.75 — confirm AML object truly absent before spend.
- arXiv 2605.27371 — Algorithmic Monocultures in Hiring — conf 0.70 — confirm no finance/AML follow-up from the same group is in flight.
