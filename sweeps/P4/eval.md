# killshot eval — P4 · "One Screener to Miss Them All" (AML monoculture)

> ## ⛔ EMPIRICAL KILL — 2026-07-16 (supersedes the provisional feasibility below)
> Two pre-registered pilots (v1 leaky battery; v2 hardened per `PREREGISTRATION_AMENDMENT.md`,
> H1–H4 from FATF/SAML-D) both KILLED on criterion 2 (measurable base rate).
> **v2 hardened result (REAL, config `45a398838805f39d`, spend $1.10, 0 ERROR):**
> pooled per-model miss = **4.4%**, bounded **≤ 6.6% (Wilson 95%)**, 21/480 misses.
> The few misses are **essentially uncorrelated** (miss-κ within 0.056 vs cross 0.060,
> contrast ≈ 0). **Feasibility FALSIFIED:** misses are too rare *and* too uncorrelated
> to estimate a joint-miss ratio affordably under BUDGET_FULL. Per the pre-committed
> outcome map (Amendment A4 §2): **P4 → drawer; T4-A "From Flips to Dollars" swaps in
> as P4.** The bounded negative is available as an optional post-filing short note.
> Novelty was never the problem; the phenomenon does not exist at measurable scale
> on realistically-serialized FATF typologies for these models.

**Topic:** P4 · **Swept:** 2026-07-15 · **Novelty:** CLEAR · **Feasibility:** ❌ FALSIFIED (empirical, 2026-07-16)
**Status line:** `Novelty: CLEAR · Feasibility: KILLED (2 pilots, pooled miss ≤6.6% CI95, misses uncorrelated) → T4-A swaps in`

> Provenance note: literature-index APIs (OpenAlex / Semantic Scholar / arXiv /
> Crossref) were unreachable from this environment, so the novelty axis was run
> as a live **web-search** sweep (see `novelty_sweep.md`) and the three
> index-count feasibility probes (P2 substrate count, P3 corpus precision,
> P5 histogram coverage) are marked **PENDING — live sweep** rather than
> fabricated. Judgment rows carry your Stage-8 overrides and render authoritative;
> the four feasibility rows are ⚠ DRAFT until a full index-backed run confirms N.

---

## Stage 8 — research-curve placement

### The 11-bucket technology-scrutiny lifecycle (modal lag = years after capability demo)

| # | Bucket | Core question | Historical origin | Modal lag |
|---|--------|---------------|-------------------|-----------|
| B1 | Capability demonstration | Can it do X at all? | every tech | 0–2y |
| B2 | Performance comparison / benchmarking | Better than the incumbent, on what metric? | Netflix RMSE | 1–4y |
| B3 | Adoption & diffusion | Who adopts, how fast, who's excluded? | digital divide; Rogers | 2–6y |
| B4 | Productivity / value realization | Does it create measured economic value? | Brynjolfsson IT paradox | 3–8y |
| B5 | Behavioral effects on individuals | Overreliance, deskilling, automation bias | Kraut Internet Paradox | 4–10y |
| B6 | Market-structure change | (Dis)intermediation, fragmentation, concentration | Menkveld; Frictionless Commerce | 4–10y |
| B7 | Critique / debunking | Was the headline benefit a measurement artifact? | filter bubble; flow-toxicity reframings | 5–12y |
| B8 | Equilibrium / strategic interaction | When everyone adopts: arms races, herding, collusion | Budish HFT arms race; Calvano | 6–15y |
| **→ ★ THIS PAPER — B9** | **Systemic risk / fragility / contagion** | **Monoculture, cascades, correlated failure** | **Kirilenko flash crash; cloud concentration** | **7–15y** |
| B10 | Distributional / equity effects | Who wins/loses; discrimination, fairness | algorithmic credit discrimination | 6–15y |
| B11 | Governance / institutional response | Liability, oversight, audit/measurement standards | Lessig Code; MiFID II; DSA | 8–20y |

### The compact 6-rung ladder (venue-targeting view)

Capability → Proliferation → Debunking → Standardization → Mechanism → ★ Consequence/Governance ★

**Position: B9 — rung 6 (Consequence/Governance).** `framework_cell` names the
bucket (B9) explicitly; the rung is inferred from the bucket mapping (systemic
risk = Consequence) and is not stated in `framework_cell`.

### ⚠ Feasibility footer (B9 = "Named but not measured")

B9 is flagged **"Named but not measured"** in the AI-in-finance saturation table
(as of Jul 2026). The strict killshot footer — *"cell is unclimbed because it is
unmeasurable in the index, not because it is open"* — fires only if P2 shows the
critical cell empty. Here the diagnosis is the **inverse**, and it is the whole
thesis: the cell is unclimbed because it is *open*, not because it is
unmeasurable. This paper is the measurement. The exact-contribution cell is
near-empty (novelty-positive), and the study is buildable because it **supplies
its own data** (SAML-D/AMLSim + FATF typology battery) rather than depending on
indexed papers — so index-emptiness of the exact cell is not a feasibility
blocker. *(Strict P2-empty check pending the live index count.)*

---

## Stage 7 — evaluation dossier

Rows are tagged **[E]** evidence-derived (mechanical from topic.yaml + the sweep +
feasibility probes) or **[J]** judgment. Your Stage-8 overrides render
authoritative; the four feasibility rows are ⚠ DRAFT pending live index counts.

| Row | Value |
|-----|-------|
| **Framework cell** [E] | B9 — systemic risk / correlated failure (measured). The exact "Named but not measured" cell in the AI-in-finance saturation map. |
| **Core question** [E] | Are LLM AML-screening misses correlated across models/institutions, and does "defense in depth" survive foundation-model monoculture? |
| **Lead finding (target)** [J·override] | Joint-miss probability is **X×** the independence benchmark; a heterogeneous second screening line recovers only **Y%** of the promised miss reduction. |
| **Foundation lit (yours to stand on)** [E] | Kleinberg–Raghavan PNAS 2021 (monoculture → correlated failure — the mechanism + null); Bommasani NeurIPS 2022 (homogenization metrics: systemic-failure ratio vs independence — the estimator scaffold); In-Context Learning for Money-Laundering Detection in Financial Graphs (arXiv 2507.14785 — graph-serialization LLM-AML precedent, citable format); SAML-D / IBM AMLSim + FATF typology catalogue (the battery). |
| **Nearest prior art & why it doesn't kill** [E] | (1) **Correlated Errors in LLMs** (arXiv 2506.07962, ICML'25) — *same formalism, 350+ models, but hiring + LLM-judge domains; no AML object* → TEMPLATE, conf 0.75. (2) **Algorithmic Monocultures in Hiring** (arXiv 2605.27371) — *monoculture homogeneity of rejections, hiring domain* → TEMPLATE, 0.70. (3) Representation Homogeneity in AI-dominated markets (2604.22818) — *markets, not screening misses* → ADJACENT. (4) Tabular CCFD adversarial transferability (2508.14699) — *gradient/tabular, classical ML* → ADJACENT. All LLM-AML papers sit at B1/B2 capability; generic flip-rate work measures per-model variance, not cross-model error correlation. |
| **Referee risk** [J·override] | Low-medium: *"synthetic typologies ≠ real laundering"* — mitigate by anchoring the battery to FATF-published typologies + SAML-D provenance; dual-use objection pre-empted by supervisory framing (measure misses, never optimize evasion). |
| **Measurability risk** [E · P1] ⚠ DRAFT | **ROBUST (provisional GREEN).** The estimand (joint-miss ratio vs independence) is clean and pre-registrable; the three alt-metrics (defense-in-depth recovery rate, Cohen's κ, systemic-failure ratio) point the same direction, so the finding does not flip under alternative operationalization. Biggest measurement threat: external validity of synthetic typologies — mitigated by FATF/SAML-D provenance. *(Confirm with the live P1 Claude call.)* |
| **Signal existence (critical cell N)** [E · P2+P5] ⚠ DRAFT | **PENDING — live index count.** Critical cell here = the measurable *substrate* (`"LLM" ("anti-money laundering" OR "transaction monitoring" OR "sanctions screening")`), expected **≥ min 25 → GREEN** (LLM-AML screening is a well-populated, actively indexed practice; the live web sweep returned many on-topic hits). The *exact-contribution* cell (cross-model AML miss-correlation) is ≈ empty — novelty-positive, not a feasibility blocker (study supplies its own data). P5 coverage expected GREEN: the LLM-AML corpus is entirely 2023+, inside the [2024, 2026] window. |
| **Corpus precision** [E · P3] ⚠ DRAFT | **PENDING — live adjudicated sweep.** Provisional GREEN: targeted vectors returned predominantly on-topic finance / AML / monoculture results (low keyword-collision rate) in the web sweep; formal on-topic % awaits an index-backed corpus. |
| **Confirmation risk** [E · P4] ⚠ DRAFT | **AMBER (soft).** The *direction* (monoculture → correlated misses) is already believed/warned — ECB/BIS third-party-concentration notices, Kleinberg–Raghavan. The *magnitude* (joint-miss ratio) and the *defense-in-depth-failure* result are not. Mitigate by foregrounding the quantitative estimand + the second-line recovery number as the contribution, not the existence of correlation. |
| **New data collection** [J·override] | Moderate: typology battery × K models × seeds × prompt variants; battery derivable from SAML-D/AMLSim, collect-once, SHA-256'd. |
| **Est. compute cost** [J·override] | ~P1-pilot scale (**< $300** gate); classification-length outputs keep tokens cheap. |
| **Regulatory hook** [J·override] | FinCEN/BSA SAR regime; FATF typologies; AMLA reform discourse; ECB/BIS monoculture + third-party-concentration warnings; SR 26-2 GenAI scope gap. |
| **Venue** [J·override] | **IEEE Access** first shot (Sarna et al. fraud review published there; its Open Issues list has zero reliability/monoculture items = gap confirmed from inside the field). Fallback: *J. Money Laundering Control* / *Finance Research Letters*. |
| **T2-1 AI/agentic jobs** [J·override] | **Strongest of slate** — fraud/AML + AI risk sits directly on your Citibank credit-risk history; authentic, not opportunistic. |
| **T2-2 Publishable** [J·override] | **High.** |
| **T2-3 Citation potential** [J·override] | **High** — fraud detection is a citation-heavy field and this is its first reliability paper; security + compliance + finance audiences. |
| **T2-4 EB-1A value** [J·override] | Adds the financial-crime pillar; completes the triangle — P4 (correlated blind spots) + P1 (decision correlation) + P5 (procyclical amplification) = one coherent "AI monoculture as systemic risk" program. |
| **Scoop risk** [E] | **HIGH.** Rule trigger: a TEMPLATE_VISIBLE at conf ≥ 0.7 (arXiv 2506.07962, *Correlated Errors in LLMs*, 0.75) → HIGH. Reinforced by a second recent template (hiring, May 2026). The monoculture template is marching domain-by-domain; AML is the obvious next stop. *(Refines your table's "medium-high": the ICML'25 correlated-errors paper is a stronger, more central template than the hiring paper.)* |
| **Dependency** [J·override] | Independent of P1–P3 (methodological continuity only); dual-use discipline is a hard design constraint; supervisory framing keeps it inside OBI scope. |
| **Sequencing** [J·override] | **Run first** — highest scoop pressure + highest job-market signal. |
| **Kill-shot verdict** [E] | ✅ **CLEAR & FEASIBLE (provisional)** — 12 vectors swept, 0 DIRECT_HIT; 3 FOUNDATION, 2 TEMPLATE_VISIBLE (both non-AML), 6 ADJACENT (all markets/forecasting/triage, non-killing). Novelty margin intact; scoop pressure HIGH → sequence first. Feasibility FEASIBLE pending confirmation of live P2/P3/P5 counts. |

---

### Human-review queue (needs_human_review = true)

- **arXiv 2506.07962 — Correlated Errors in Large Language Models** (ICML'25; Kim, Peng, N. Garg). 350+ LLMs; error correlation driven by shared architecture/provider; downstream on hiring + LLM-judge. *Review:* confirm the AML/screening object is genuinely unoccupied before committing spend — this is the paper a referee will cite as prior art.
- **arXiv 2605.27371 — Algorithmic Monocultures in Hiring** (Bommasani, Bana, Creel, Jurafsky, Liang). 3M applicants; individual + group homogeneity of rejections. *Review:* confirm no finance/AML follow-up from the same group is in flight.

### Auto-verdict

`CLEAR` — no DIRECT_HIT; 2 TEMPLATE_VISIBLE flags pending your human review. Set
the final verdict with `killshot verdict P4 clear --note "..."` after clearing
the queue. Then run a full index-backed sweep to convert the ⚠ DRAFT feasibility
rows (P2/P3/P5) from provisional to confirmed.
