"""Defense-in-depth recovery rate. A two-line system (primary P + second-line S)
misses a suspicious case only if BOTH miss it. Under independence the promised
residual is p_P·p_S; correlation inflates the observed residual, so the second
line recovers only a fraction of the promised miss-reduction.

recovery ρ(P,S) = (p_P − res_obs) / (p_P − p_P·p_S)
  ρ = 1  ⇔ second line delivers exactly what independence promised
  ρ < 1  ⇔ correlation ate part of the protection (the paper's finding)
  ρ ≤ 0  ⇔ the heterogeneous second line added no net protection

Headline = mean ρ over HETEROGENEOUS (cross-family) pairs, contrasted with the
HOMOGENEOUS (same-family) mean.
"""
from __future__ import annotations
from itertools import permutations
from miss import MissTable
import correlation as X


def pair_recovery(mt: MissTable, primary: str, second: str, cases: list[str]) -> dict:
    support = [c for c in cases
               if mt.miss[primary].get(c) is not None and mt.miss[second].get(c) is not None]
    if not support:
        return {"n": 0, "recovery": None}
    p_P = X.marginal_miss(mt, primary, support)
    p_S = X.marginal_miss(mt, second, support)
    res_obs = sum(mt.miss[primary][c] == 1 and mt.miss[second][c] == 1
                  for c in support) / len(support)
    res_ind = p_P * p_S
    red_ind = p_P - res_ind
    red_obs = p_P - res_obs
    recovery = (red_obs / red_ind) if red_ind > 1e-12 else None
    return {"n": len(support), "primary": primary, "second": second,
            "family_primary": mt.family[primary], "family_second": mt.family[second],
            "heterogeneous": mt.family[primary] != mt.family[second],
            "p_primary": p_P, "p_second": p_S,
            "residual_independence": res_ind, "residual_observed": res_obs,
            "reduction_promised": red_ind, "reduction_observed": red_obs,
            "recovery": recovery}


def all_pairs(mt: MissTable, models: list[str], cases: list[str]) -> list[dict]:
    """Ordered (primary, second) pairs, primary != second."""
    return [pair_recovery(mt, p, s, cases) for p, s in permutations(models, 2)]


def summary(mt: MissTable, models: list[str], cases: list[str]) -> dict:
    pairs = all_pairs(mt, models, cases)
    het = [r["recovery"] for r in pairs if r["heterogeneous"] and r["recovery"] is not None]
    hom = [r["recovery"] for r in pairs if not r["heterogeneous"] and r["recovery"] is not None]

    def _m(xs): return (sum(xs) / len(xs)) if xs else None
    return {
        "heterogeneous_recovery_mean": _m(het),
        "homogeneous_recovery_mean": _m(hom),
        "n_heterogeneous_pairs": len(het), "n_homogeneous_pairs": len(hom),
        "pairs": pairs,
    }


def het_recovery_scalar(mt: MissTable, models: list[str], cases: list[str]) -> float | None:
    """Mean heterogeneous recovery — the bootstrap target scalar."""
    return summary(mt, models, cases)["heterogeneous_recovery_mean"]
