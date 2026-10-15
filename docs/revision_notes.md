# Revision — Discover Artificial Intelligence, submission be7bd75c-daba-4386-ad14-beac2bbcac64

Round 1 referee response. Editor + three reviewers; Reviewer 1 recommends acceptance,
Reviewer 2 minor revision (13 numbered comments in an attachment), Reviewer 3 one major
comment. The editor, Reviewer 2 (#5) and Reviewer 3 all raise the same issue: the
preregistered per-case aggregation rule (decision D4) resolved 2-2 replicate ties by
reference to the ground-truth label.

## Files

| file | role |
|---|---|
| `reviewer_comments_verbatim.txt` | **Authoritative** raw editor/reviewer text. Never edit. R2's comments are from the uploaded `.docx` attachment. |
| `RESPONSE_TO_REVIEWERS.tex` / `.pdf` | Point-by-point letter, Paper 2 format. Every concern quoted verbatim in green, then Author response and Author action. |
| `check_verbatim.py` | Gate: asserts every reviewer sentence in the raw file survives into the compiled PDF. Exit 0 / 1 / 2. |
| `check_docx_citations.py` | Gate: rejects any citation rendering inside an em-dash aside in the converted Word file (R2 #13). Exit 0 / 1 / 2. |
| `check_binding.py` | Gate: binds 23 load-bearing manuscript numbers to the result that produced them, by anchor phrase. Exit 0 / 1 / 2. |
| `analysis/` | Standalone recomputation of all reported figures. |

## Status

The letter's **Author response** blocks state findings that are already computed and
verified. The **Author action** blocks describe manuscript edits that have **not yet been
made** — `manuscript/latex/main.tex` is untouched by this revision so far.

## Analysis scripts

Run from anywhere; they read the frozen capture corpus at
`../capsule/data/capture/runs_full_*.csv` by absolute path and deliberately **do not
import** `capsule/code/src/*`, so the figures are an independent re-derivation rather
than a re-run of the submission's own code.

| script | produces |
|---|---|
| `analysis/tie_policies.py` | FP and miss rates under 5 aggregation rules; per-model tie census |
| `analysis/more.py` | valid-call distribution, Cochran Q, pairwise McNemar, single-call configurations |
| `analysis/final.py` | cluster-bootstrap spread CIs (repo's own estimator), prevalence sweep |
| `analysis/trend.py` | adjacent-tier paired McNemar, cluster-robust step CIs, cluster permutation test |

## Headline result of the re-analysis

The cross-model false-positive spread is **77.7 to 85.3 pp across all nine analyses**
(five aggregation rules, four single-call configurations) and the model ordering is
identical in every one. New primary rule (ties escalate, label-independent): spread
**83.3 pp, 95% CI 71.8-93.7**, Cochran Q = 117.0, p = 2.3e-24.

D4's benign branch was already a strict majority, so a label-independent strict-majority
rule reproduces **every published false-positive rate exactly**; the label dependence
affected only the miss-side numbers.

## Five defects found during the re-analysis

1. `capsule/code/src/classification.py` writes the Cochran p-value as `1 - chi2.cdf(Q, df)`,
   which **underflows to 0.0** at Q = 131.553. Deposited `stats_tests.json` therefore records
   `p: 0.0` and cannot reproduce the manuscript's 2e-27. `chi2.sf` gives 1.812e-27 — the
   manuscript is right, the archive is wrong.
2. That module's method string says `"modal vote, ties->flag (D4)"`. True of the suspicious
   branch only; on benign cases ties go to **no** flag — and it is written into the deposited
   `classification_metrics.json`.

3. **Undisclosed deviation from preregistered decision D4.** D4 (`capsule/docs/decisions_log.md:45`),
   `preregistration.md:169` and `preregistration_pivot.md:38` all specify the modal decision with
   **ties broken toward flag**, with no reference to the case label. The implemented benign branch
   required a strict majority. The label-independent rule all three reviewers request *is* the
   preregistered rule. The deviation understated every published false-positive rate (0.3/1.0/23.7/24.7/83.0
   against the preregistered 2.3/7.7/37.0/44.0/85.7); the spread was almost unaffected (82.7 vs 83.3 pp).
   Appendix A's sentence attributing a label-dependent rule to preregistration is therefore incorrect.

4. **Every small p-value in the deposit was recorded as exactly `0.0`.** `_round4` in
   `classification.py` rounds to 4 decimal places, so the Cochran p and **8 of 10** pairwise
   McNemar p-values were serialised as `0.0`. Fixed to keep 4 significant figures below 1e-4,
   which is still deterministic; byte-identical re-runs are unaffected.

5. **`main.tex:87` overstates the deposit.** It says the model served behind each Google alias
   "is recorded in the archived per-call response metadata". It is not: the capture rows, the probe
   receipts (`capsule/docs/probe_receipts.json`) and the freeze receipts all record only the alias
   strings `gemini-flash-latest` / `gemini-flash-lite-latest`. No resolved version was captured.
   The Limitations (line 207) state the position correctly; the Methods sentence does not.

## Gate verification

`check_verbatim.py` was fault-injected before being trusted:

`check_verbatim.py`:

| fault | expected | observed |
|---|---|---|
| one reviewer sentence silently reworded | exit 1 | exit 1 |
| an entire reviewer concern block deleted | exit 1 | exit 1 |
| compiled PDF absent | exit 2 (not 0) | exit 2 |
| unmodified letter | exit 0 | exit 0, 65 sentences checked |

`check_docx_citations.py`:

| fault | expected | observed |
|---|---|---|
| a citation returned to the inside of an em-dash aside | exit 1 | exit 1 |
| converted Word file absent | exit 2 (not 0) | exit 2 |
| manuscript as fixed | exit 0 | exit 0 |

`check_binding.py`:

| fault | expected | observed |
|---|---|---|
| two real model FP rates swapped (defeats any coverage test) | exit 1 | exit 1, 2 rules |
| spread changed to a value no result equals | exit 1 | exit 1 |
| results file absent | exit 2 (not 0) | exit 2 |
| manuscript as revised | exit 0 | exit 0, 23 rules bound |

Capsule hash check: mutating a hashed output is detected and a re-run restores it.

An earlier version of `check_docx_citations.py` also flagged a citation placed immediately
*before* an opening em dash — the correct placement. It was removed: a gate that fires on the
right answer would have forced a wrong fix.

## Manuscript and capsule: revision implemented

All `Author action` items in the letter are implemented. `main.tex` is 31 pages (was 26).

**Capsule.** The aggregation rule now has exactly one implementation, `code/src/aggregate.py`
(preregistered D4: modal flag, ties to flag, label-independent). `miss.py` and
`classification.py` delegate to it; a dead duplicate in `altrisk.py` was removed. New modules:
`aggregation_sensitivity.py` (five policies, four single-call configurations, tie census,
adjacent-tier tests, cluster permutation, prevalence sweep) and `figures.py` (all six figures,
which previously had **no generator at all** and could not be re-derived). Both are wired into
`reproduce.py` and hashed. Tests: 5 pass, including three new guards (label-independence of the
rule, small p-values surviving serialisation, sensitivity output emitted).

**Headline changes under the restored rule**

| quantity | as submitted | preregistered D4 |
|---|---|---|
| FP rates | 0.3 / 1.0 / 23.7 / 24.7 / 83.0 | 2.3 / 7.7 / 37.0 / 44.0 / 85.7 |
| FP spread | 82.7 pp (69.2-95.3) | **83.3 pp (71.8-93.7)** |
| Cochran Q | 131.6 | 117.0, p = 2.327e-24 |
| disagreement on legitimate | 85.7% | 88.7% |
| miss rates | unchanged | unchanged |
| alert ratio at 0.1% | 197-fold | 35-fold aggregate; **36-196-fold deployable** |

The alert-volume headline is now reported as the range across deployable single-call
configurations, because the ratio is driven by the prompt (terse ~195-fold, FATF ~36-fold)
rather than by the aggregation rule. Model ordering is invariant across all nine analyses,
both prompts, both seeds and prevalence 0.01-1%.

## Price verification (R2 #10)

OpenAI list prices in the registry are correct, confirmed against the OpenAI pricing docs
(accessed 2026-10-13): GPT-4o $2.50/$10.00, GPT-4o-mini $0.15/$0.60, GPT-4.1-mini $0.40/$1.60
per 1M input/output tokens. The two Google figures ($0.50/$3.00 and $0.15/$0.60) are **not**
list prices — `models.yaml` states they are conservative placeholders overwritten by measured
cost. They cannot be recovered for July 2026 either, because the aliases' resolved versions were
never captured and the current pricing page no longer lists those versions. Tier should therefore
rest on the verified OpenAI prices plus the measured per-call costs in the archived ledger
(GPT-4o $0.002108, Gemini Flash $0.000536, GPT-4.1-mini $0.000342, Flash-Lite $0.000148,
GPT-4o-mini $0.000125), which reproduce the tier ordering without an unverifiable price.
