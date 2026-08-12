"""Pilot verdict writer. Reads claims.json (produced by analysis/run.py) and writes
pilot/PILOT_RESULTS.md (the numbers) and pilot/PILOT_VERDICT.md (the three
pre-registered PASS criteria, each GREEN/RED, ending in exactly one verdict line).
Never decides to run the full grid — it only reports and stops.

  python pilot/verdict.py [--claims ../claims.json]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CLAIMS = _HERE.parent / "claims.json"


def _fmt(x, nd=3):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _ci(pair, nd=2):
    if not pair or pair[0] is None or pair[1] is None:
        return "[n/a]"
    return f"[{pair[0]:.{nd}f}, {pair[1]:.{nd}f}]"


def build(claims: dict) -> tuple[str, str, str]:
    m = claims["meta"]
    g = claims["pilot_gate"]
    pj = claims["primary_joint_miss"]
    wc = claims["within_vs_cross_family"]
    dd = claims["defense_in_depth"]

    c1 = bool(g["criterion_1_ran_clean"]) and m["n_error"] == 0
    c2 = bool(g["criterion_2_base_rate_in_band"])
    c3 = bool(g["criterion_3_signal"]) and bool(g["criterion_3_contrast_computable"])

    mb = claims.get("miss_rate_bounds", {})
    up = mb.get("pooled_miss_upper95_wilson")
    r3 = mb.get("pooled_rule_of_three_upper")
    bound_txt = ""
    if g["pooled_miss_rate"] is not None and g["pooled_miss_rate"] < 0.10:
        parts = []
        if up is not None:
            parts.append(f"pooled miss ≤ {up*100:.1f}% (Wilson 95%)")
        if r3 is not None:
            parts.append(f"rule-of-three ≤ {r3*100:.1f}%")
        if parts:
            bound_txt = " — bounded: " + "; ".join(parts)

    # verdict precedence: variance-KILL > operational-FAIL > signal-FAIL > PASS
    if not c2:
        verdict = (f"PILOT: KILL (criterion 2 — pooled miss rate "
                   f"{_fmt(g['pooled_miss_rate'])} out of the 0.10-0.70 measurable band; "
                   f"no variance to correlate{bound_txt})")
    elif not c1:
        verdict = f"PILOT: FAIL (criterion 1 — did not run clean: error_rate={_fmt(m['error_rate'])}, spend=${_fmt(g['spend_usd'],4)}/cap ${_fmt(m['budget_cap_usd'],2)})"
    elif not c3:
        verdict = "PILOT: FAIL (criterion 3 — cross-model joint-miss signal not estimable, or ratio <= independence, or within/cross contrast not computable)"
    else:
        verdict = "PILOT: PASS → cleared for full run"

    def mark(ok): return "🟢 GREEN" if ok else "🔴 RED"

    verdict_md = f"""# PILOT_VERDICT — P4

**Subgrid:** `{m['subgrid']}`  ·  **Mode:** `{m['mode']}`  ·  **Config hash:** `{m['config_hash']}`
**Models:** {', '.join(m['models'])}
**Battery:** pilot sha256 `{m['battery_sha256'].get('pilot','n/a')[:16]}...`  ·  **Analysis seed:** {m['analysis_seed']}  ·  **Bootstrap draws:** {m['bootstrap_draws']}

> Pre-registered pilot gate (PREREGISTRATION §5). All three must hold to clear the
> full run. This file only reports; it never starts the full run.

## Criterion 1 — Ran clean  {mark(c1)}
End-to-end, resumable, **{m['n_error']} ERROR** records ({_fmt(m['error_rate'])} rate),
total spend **${_fmt(g['spend_usd'],4)}** ≤ cap **${_fmt(m['budget_cap_usd'],2)}**.
Rows captured: {m['n_rows']}.

## Criterion 2 — Measurable base rate  {mark(c2)}
Pooled per-model miss (false-negative) rate = **{_fmt(g['pooled_miss_rate'])}**,
target band **[0.10, 0.70]**. {'Inside band — variance exists to correlate.' if c2 else 'OUT OF BAND — nothing to correlate → KILL.'}
{('**Bound (Amendment A3):**' + bound_txt.replace(' — bounded:', '') + f". Pooled misses {mb.get('pooled_misses')}/{mb.get('pooled_n')}. A clean/near-zero sweep is a quantified upper bound on the true miss rate, not an ambiguous null.") if bound_txt else ''}

## Criterion 3 — Estimable correlation with signal  {mark(c3)}
Cross-model joint-miss ratio (observed / independence) = **{_fmt(pj['ratio'],2)}**,
95% CI **{_ci(pj['ratio_ci95'])}** (excludes 1: **{pj['ci_excludes_1']}**).
J_observed = {_fmt(pj['j_observed'],4)} vs J_independence = {_fmt(pj['j_independence'],4)}.
Within-family vs cross-family κ contrast = **{_fmt(wc['contrast'])}**
(within {_fmt(wc['within_family_mean'])} − cross {_fmt(wc['cross_family_mean'])}),
CI {_ci(wc['contrast_ci95'])} — contrast computable: **{g['criterion_3_contrast_computable']}**.

---

## {verdict}
"""

    results_md = f"""# PILOT_RESULTS — P4  (mode={m['mode']})

Config hash `{m['config_hash']}` · battery(pilot) `{m['battery_sha256'].get('pilot','n/a')[:16]}...` · seed {m['analysis_seed']} · draws {m['bootstrap_draws']}.
{m['n_rows']} rows, {m['n_error']} ERROR ({_fmt(m['error_rate'])}), spend ${_fmt(g['spend_usd'],4)}.
Suspicious cases: {m['n_suspicious_cases']} · common support: {m['n_common_support']}.

## Headline estimands
| Estimand | Point | 95% CI |
|---|---|---|
| Joint-miss ratio R (primary) | {_fmt(pj['ratio'],2)} | {_ci(pj['ratio_ci95'])} |
| J_observed | {_fmt(pj['j_observed'],4)} | {_ci(pj['j_observed_ci95'],4)} |
| J_independence | {_fmt(pj['j_independence'],4)} | — |
| Systemic-failure ratio (Bommasani) | {_fmt(claims['systemic_failure_ratio']['value'],2)} | — |
| Heterogeneous 2nd-line recovery | {_fmt(dd['heterogeneous_recovery_mean'])} | {_ci(dd['heterogeneous_recovery_ci95'])} |
| Homogeneous 2nd-line recovery | {_fmt(dd['homogeneous_recovery_mean'])} | — |
| Within−cross family κ contrast | {_fmt(wc['contrast'])} | {_ci(wc['contrast_ci95'])} |
| Pooled per-model miss rate | {_fmt(g['pooled_miss_rate'])} | — |

## Per-model marginal miss rate
| model | family | miss rate | n | Wilson CI |
|---|---|---|---|---|
""" + "\n".join(
        f"| {mk} | {v['family']} | {_fmt(v['miss_rate'])} | {v['n']} | {_ci(v['wilson_ci'])} |"
        for mk, v in claims["marginal_miss_rates"]["per_model"].items()
    ) + f"""

## Pairwise Cohen κ on misses
| pair | κ |
|---|---|
""" + "\n".join(
        f"| {k} | {_fmt(v)} |" for k, v in claims["pairwise_agreement_on_misses"]["kappa_matrix"].items()
    ) + f"""

## Robustness
Prevalence/churn: {claims['robustness']['prevalence_churn']}.
Chance-corrected agreement is reported under three statistics (κ, Scott π, Gwet AC1)
in claims.json; a finding that flipped sign across them would be flagged non-robust.

> {'MOCK data — pipeline validation only, NOT a scientific result (DECISIONS D9).' if m['mode']=='MOCK' else 'REAL capture.'}
"""
    return verdict, verdict_md, results_md


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", default=str(_CLAIMS))
    args = ap.parse_args()
    claims = json.loads(Path(args.claims).read_text())
    verdict, verdict_md, results_md = build(claims)
    (_HERE / "PILOT_VERDICT.md").write_text(verdict_md)
    (_HERE / "PILOT_RESULTS.md").write_text(results_md)
    print(verdict_md)
    print("\n" + "=" * 70)
    print(verdict)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
