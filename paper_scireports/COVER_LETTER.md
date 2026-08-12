# Cover letter — Scientific Reports

Samir Chincholikar¹ and Robin Chawla¹*
¹ Independent Researcher
*Corresponding author: Robin Chawla — robin.chawla.cse14@iitbhu.ac.in (Co-author: samir.chincholikar@gmail.com)

To the Editors, *Scientific Reports*

Dear Editors,

I am pleased to submit our manuscript, **"The choice of foundation model determines the false-positive burden of large language model anti-money-laundering transaction screening,"** for consideration as an Article in *Scientific Reports*.

**What we show.** Large language models (LLMs) are being adopted to screen financial transactions for money laundering, yet the field has evaluated them only for accuracy, treating "an LLM" as an interchangeable component. We instead ask what happens when the *same* screening task is given to *different* foundation models. On an identical, preregistered battery of 600 synthetic cases anchored to FATF laundering typologies, the rate at which five widely used models raised a false alarm on legitimate transactions ranged from 0.3% to 83.0% — an 83-percentage-point spread (Cochran's Q = 131.6, P ≈ 2×10⁻²⁷) — and the models disagreed on 86% of legitimate cases. Critically, the variation is systematic: within each provider, false-alarm rates fall monotonically as capability rises, so the smallest, cheapest models over-flag far more than their flagship siblings (83.0% for GPT-4o-mini vs 1.0% for GPT-4o) — meaning the common cost-saving move of substituting a cheaper model predictably pushes a deployment toward a high-false-positive regime. Projected to realistic prevalence, the choice of model changes analyst alert workload by roughly two-hundred-fold on identical activity. Because the model behind a commercial API can change without notice, this operating point is an unmanaged model risk.

**Why it is appropriate for *Scientific Reports*.** The work is technically sound, rigorously quantified, and broadly significant across the journal's readership. It sits at the intersection of machine learning, financial technology and governance, and speaks to a general-science audience concerned with the reliability and oversight of AI systems deployed in high-stakes settings — a topic of active interest well beyond the AML community, and adjacent to recent *Scientific Reports* work on machine-learning fraud detection. The contribution is a measurement and a governance implication rather than a new classifier, and it is fully reproducible: the manuscript is accompanied by a preregistration, the complete frozen dataset, and a one-command reproducible capsule that regenerates and hash-verifies the data and recomputes every reported number byte-identically.

**Rigour and openness.** The analysis was preregistered; all statistics use tests appropriate to the paired design (Cochran's Q, McNemar's exact test with Bonferroni correction, Wilson intervals, and a cluster bootstrap), with exact P-values and 95% confidence intervals reported throughout. We also report a preregistered secondary null result (no correlated misses across models), and we include non-LLM baselines (a rules heuristic and a supervised classifier) as a reference frame.

**Declarations.** This is original work, not under consideration elsewhere. It used only synthetic data (no human participants or animals). The authors declare no competing interests. We have not had prior discussions with a *Scientific Reports* Editorial Board Member about this work.

**Suggested reviewers** (no conflict of interest with the author):
- *[Name, affiliation, email — an expert in AI reliability/evaluation]*
- *[Name, affiliation, email — an expert in AML/financial-crime analytics]*
- *[Name, affiliation, email — an expert in model risk management / algorithmic governance]*

**Opposed reviewers:** none.

Thank you for considering our submission.

Sincerely,
Robin Chawla (corresponding author, on behalf of both authors)

*(Authors to complete the three suggested-reviewer entries before submission.)*
