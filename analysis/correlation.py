"""Correlation layer: marginal miss rates, independence-predicted vs observed
joint-miss and their ratio, pairwise chance-corrected agreement on misses (Cohen
κ / Scott π / Gwet AC1), the systemic-failure ratio (Bommasani), the within- vs
cross-family correlation contrast, and a prevalence-vs-churn decomposition.

All functions take the MissTable and a list of case_ids (the support / a bootstrap
resample) and return plain floats/dicts — pure and order-independent.
"""
from __future__ import annotations
from itertools import combinations
from miss import MissTable


def _vec(mt: MissTable, model: str, cases: list[str]) -> list[int]:
    return [mt.miss[model][c] for c in cases]


def marginal_miss(mt: MissTable, model: str, cases: list[str]) -> float | None:
    v = [x for c in cases if (x := mt.miss[model].get(c)) is not None]
    return (sum(v) / len(v)) if v else None


def marginals(mt: MissTable, models: list[str], cases: list[str]) -> dict[str, float]:
    return {m: marginal_miss(mt, m, cases) for m in models}


def joint_miss(mt: MissTable, models: list[str], cases: list[str]) -> dict:
    """Observed vs independence-predicted joint-miss over `cases` (assumed common
    support). J_obs = mean over cases of Π_m miss; J_ind = Π_m p_m; ratio = J_obs/J_ind."""
    if not cases:
        return {"j_obs": None, "j_ind": None, "ratio": None, "n": 0}
    p = marginals(mt, models, cases)
    if any(v is None for v in p.values()):
        return {"j_obs": None, "j_ind": None, "ratio": None, "n": len(cases)}
    j_obs = sum(all(mt.miss[m][c] == 1 for m in models) for c in cases) / len(cases)
    j_ind = 1.0
    for m in models:
        j_ind *= p[m]
    ratio = (j_obs / j_ind) if j_ind > 0 else None
    return {"j_obs": j_obs, "j_ind": j_ind, "ratio": ratio, "n": len(cases),
            "marginals": p}


def systemic_failure_ratio(mt: MissTable, models: list[str], cases: list[str]) -> float | None:
    """Bommasani homogenization metric: observed / independence-expected joint
    failure for the full model set. Numerically the primary joint-miss ratio."""
    return joint_miss(mt, models, cases)["ratio"]


# ── pairwise chance-corrected agreement on the binary MISS label ────────────
def _pair_counts(mt: MissTable, a: str, b: str, cases: list[str]):
    n = a11 = a00 = a10 = a01 = 0
    for c in cases:
        xa, xb = mt.miss[a].get(c), mt.miss[b].get(c)
        if xa is None or xb is None:
            continue
        n += 1
        if xa == 1 and xb == 1: a11 += 1
        elif xa == 0 and xb == 0: a00 += 1
        elif xa == 1 and xb == 0: a10 += 1
        else: a01 += 1
    return n, a11, a00, a10, a01


def agreement(mt: MissTable, a: str, b: str, cases: list[str]) -> dict:
    """Cohen κ, Scott π, Gwet AC1 for two models' miss labels over `cases`."""
    n, a11, a00, a10, a01 = _pair_counts(mt, a, b, cases)
    if n == 0:
        return {"n": 0, "po": None, "kappa": None, "scott_pi": None, "gwet_ac1": None}
    po = (a11 + a00) / n
    pa1 = (a11 + a10) / n          # rater a "miss" rate
    pb1 = (a11 + a01) / n          # rater b "miss" rate
    # Cohen
    pe_c = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    kappa = (po - pe_c) / (1 - pe_c) if pe_c < 1 else None
    # Scott π (pooled marginal)
    p1 = (pa1 + pb1) / 2
    pe_s = p1 * p1 + (1 - p1) * (1 - p1)
    scott = (po - pe_s) / (1 - pe_s) if pe_s < 1 else None
    # Gwet AC1
    q = (a11 * 2 + a10 + a01) / (2 * n)
    pe_g = 2 * q * (1 - q)
    ac1 = (po - pe_g) / (1 - pe_g) if pe_g < 1 else None
    return {"n": n, "po": po, "kappa": kappa, "scott_pi": scott, "gwet_ac1": ac1}


def pairwise_matrix(mt: MissTable, models: list[str], cases: list[str], stat: str = "kappa") -> dict:
    out = {}
    for a, b in combinations(models, 2):
        out[f"{a}|{b}"] = agreement(mt, a, b, cases)[stat]
    return out


def within_cross_contrast(mt: MissTable, models: list[str], cases: list[str],
                          stat: str = "kappa") -> dict:
    """Mean pairwise agreement (stat) among same-family pairs vs cross-family pairs,
    plus the contrast (within - cross) and the mean pairwise joint-miss ratio in
    each class."""
    within, cross = [], []
    within_r, cross_r = [], []
    for a, b in combinations(models, 2):
        val = agreement(mt, a, b, cases)[stat]
        pair_support = [c for c in cases
                        if mt.miss[a].get(c) is not None and mt.miss[b].get(c) is not None]
        jr = joint_miss(mt, [a, b], pair_support)["ratio"]
        same = mt.family[a] == mt.family[b]
        (within if same else cross).append(val)
        (within_r if same else cross_r).append(jr)

    def _m(xs):
        xs = [x for x in xs if x is not None]
        return (sum(xs) / len(xs)) if xs else None
    w, c = _m(within), _m(cross)
    return {
        "stat": stat,
        "within_family_mean": w, "cross_family_mean": c,
        "contrast": (w - c) if (w is not None and c is not None) else None,
        "n_within_pairs": len(within), "n_cross_pairs": len(cross),
        "within_family_joint_ratio_mean": _m(within_r),
        "cross_family_joint_ratio_mean": _m(cross_r),
    }


def prevalence_churn(mt: MissTable, models: list[str], cases: list[str]) -> dict:
    """Decompose cross-model miss disagreement into a prevalence component (models
    differ in overall miss rate) and a churn component (they miss DIFFERENT cases
    at matched rates), averaged over model pairs.

    For a pair: disagreement = (a10+a01)/n; prevalence(bias) = |a10-a01|/n; churn =
    2*min(a10,a01)/n. The monoculture claim rests on co-miss exceeding independence
    even net of prevalence — quantified alongside by the joint-miss ratio."""
    dis, prev, churn = [], [], []
    spreads = []
    p = marginals(mt, models, cases)
    vals = [v for v in p.values() if v is not None]
    prevalence_spread = (max(vals) - min(vals)) if vals else None
    for a, b in combinations(models, 2):
        n, a11, a00, a10, a01 = _pair_counts(mt, a, b, cases)
        if n == 0:
            continue
        dis.append((a10 + a01) / n)
        prev.append(abs(a10 - a01) / n)
        churn.append(2 * min(a10, a01) / n)
    def _m(xs): return (sum(xs) / len(xs)) if xs else None
    return {"mean_disagreement": _m(dis), "mean_prevalence_component": _m(prev),
            "mean_churn_component": _m(churn), "marginal_miss_spread": prevalence_spread}
