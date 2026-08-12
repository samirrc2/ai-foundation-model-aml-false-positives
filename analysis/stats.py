"""Inferential layer: a seeded CLUSTER BOOTSTRAP resampling the clustering unit =
typology stratum. Any headline scalar is a function of a list of suspicious
case_ids; the bootstrap resamples strata with replacement, concatenates their
cases, recomputes the scalar, and returns point + 95% percentile CI. Byte-stable
given the same frozen inputs and seed.
"""
from __future__ import annotations
import math
import random
from miss import MissTable


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n == 0:
        return (None, None)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return (center - half, center + half)


def cluster_bootstrap(mt: MissTable, cases: list[str], stat_fn, draws: int = 2000,
                      seed: int = 4242) -> dict:
    """stat_fn(case_ids) -> float|None. Resamples typology strata with replacement."""
    by_stratum = mt.cases_by_stratum(cases)
    strata = sorted(by_stratum)
    n = len(strata)
    point = stat_fn(cases)
    if n == 0:
        return {"point": point, "ci_low": None, "ci_high": None, "n_strata": 0, "n_valid": 0}
    rng = random.Random(seed)
    vals = []
    for _ in range(draws):
        resampled = []
        for _i in range(n):
            resampled.extend(by_stratum[strata[rng.randrange(n)]])
        v = stat_fn(resampled)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    vals.sort()
    if len(vals) < 20:
        return {"point": point, "ci_low": None, "ci_high": None,
                "n_strata": n, "n_valid": len(vals)}
    return {"point": point,
            "ci_low": vals[int(0.025 * len(vals))],
            "ci_high": vals[int(0.975 * len(vals)) - 1],
            "n_strata": n, "n_valid": len(vals)}


def ci_excludes(ci: dict, value: float, side: str = "above") -> bool | None:
    """True if the CI lies strictly on one side of `value`. side='above' => whole CI
    > value (e.g. ratio > 1); side='below' => whole CI < value (e.g. recovery < 1)."""
    lo, hi = ci.get("ci_low"), ci.get("ci_high")
    if lo is None or hi is None:
        return None
    return (lo > value) if side == "above" else (hi < value)
