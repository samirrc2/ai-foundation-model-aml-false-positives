# Cover letter — Discover Artificial Intelligence

Samir Chincholikar¹ and Robin Chawla¹*
¹ Independent Researcher
*Corresponding author: Robin Chawla — robin.chawla.cse14@iitbhu.ac.in (Co-author: samir.chincholikar@gmail.com)

To the Editors, *Discover Artificial Intelligence*

Dear Editors,

We are pleased to submit our manuscript, **"Same Transactions, Different Alarms: Foundation-Model Choice and AML False Positives,"** for consideration as a **Research** article in *Discover Artificial Intelligence*.

**Context and importance.** Large language models (LLMs) are increasingly being deployed to screen financial transactions for money laundering, yet the field has evaluated them almost entirely for accuracy, treating "an LLM" as an interchangeable component. Our study asks a question that this framing hides: what happens when the *same* screening task is handed to *different* foundation models? On an identical, preregistered battery of 600 synthetic cases anchored to recognised laundering typologies — half of them legitimate transactions engineered to resemble alerts — the rate at which five widely used commercial models raised a false alarm on legitimate activity ranged from 0.3% to 83.0%, a spread of 83 percentage points (Cochran's Q = 131.6, P ≈ 2×10⁻²⁷), with the models disagreeing on 86% of legitimate cases. The variation is systematic rather than noisy: within each provider the false-alarm rate falls monotonically as model tier rises, so the routine cost-saving move of substituting a smaller, cheaper model predictably pushes a deployment toward a high-false-positive regime. Projected to realistic prevalence, the choice of model alone changes analyst alert workload roughly two-hundred-fold on identical activity. Because the model behind a commercial API can change without notice, this operating point is an unmanaged model risk that current oversight does not capture.

**Why it is appropriate for *Discover Artificial Intelligence*.** The work sits squarely within the journal's scope at the intersection of applied machine learning, financial technology, and AI governance, and it speaks directly to the journal's active line of AI-in-finance research — including recent *Discover Artificial Intelligence* articles on financial fraud detection, enterprise financial-risk prediction, and trustworthy, transparent AI. Our contribution is a rigorous measurement and its governance implication rather than a new classifier: we bring paired statistical inference (Cochran's Q, McNemar's exact test with Bonferroni correction, Wilson score intervals, and a cluster bootstrap) and full confidence intervals to a question the literature has evaluated only with point estimates, and we report non-LLM baselines (a rules heuristic and a supervised classifier) as a reference frame.

**Rigour and openness.** The analysis was preregistered. The manuscript is accompanied by the complete frozen dataset (a 12,000-call capture), the preregistration and its amendment history, and a one-command reproducible capsule that regenerates and hash-verifies the data and recomputes every reported number byte-identically, offline and at zero cost. We also report a preregistered secondary null result (no correlated misses across models).

**Declarations.** This is original work, not published before and not under consideration elsewhere. It used only synthetic data (no human participants, human tissue, or animals). No funding was received. The authors declare no competing interests. All data and code are openly available (see the Data Availability statement in the manuscript).

Thank you for considering our submission.

Sincerely,
Robin Chawla (corresponding author, on behalf of both authors)
