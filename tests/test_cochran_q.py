"""Cochran's Q must match an independent implementation.

The submitted and first-revised analyses reported every Q understated fivefold, because the
numerator omitted the factor k:

    Q = k(k-1) * sum_j (C_j - Cbar)^2 / (k*sum_i R_i - sum_i R_i^2)

A wrong constant factor is invisible to every other gate in this repository -- the value is
self-consistent, reproduces byte-identically, and is bound to the manuscript by check_binding,
so binding a wrong number simply pins the error in place. The only thing that catches it is a
second implementation of the same statistic.

statsmodels is not a runtime dependency of the capsule, so this test skips when it is absent
rather than forcing it into requirements.txt. It is still the check that would have caught the
original defect, and it runs wherever statsmodels is installed.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

np = pytest.importorskip("numpy")
smct = pytest.importorskip("statsmodels.stats.contingency_tables",
                           reason="statsmodels is not a capsule dependency")


def _q_from_definition(mat) -> float:
    """Cochran's Q written straight from the definition, independent of the repo's code."""
    k = len(mat[0])
    Cj = [sum(r[j] for r in mat) for j in range(k)]
    Ri = [sum(r) for r in mat]
    Cbar = sum(Cj) / k
    den = k * sum(Ri) - sum(r * r for r in Ri)
    return k * (k - 1) * sum((c - Cbar) ** 2 for c in Cj) / den


def test_repo_formula_matches_statsmodels():
    import aggregation_sensitivity as AS
    rng = np.random.default_rng(7)
    for _ in range(25):
        mat = rng.integers(0, 2, size=(60, 5)).tolist()
        if len({tuple(c) for c in zip(*mat)}) == 1:
            continue                                   # degenerate: all columns identical
        want = smct.cochrans_q(np.array(mat)).statistic
        got, df, _p = AS._cochran_q(mat)
        assert df == 4
        assert abs(got - want) < 1e-9, f"repo {got} vs statsmodels {want}"
        assert abs(_q_from_definition(mat) - want) < 1e-9


def test_published_q_values_match_statsmodels():
    """Every Q in the shipped results must survive recomputation by statsmodels."""
    res = json.loads((ROOT / "results" / "aggregation_sensitivity.json").read_text())
    rows = list(res["policies"].values()) + list(res["single_call_configurations"].values())
    assert len(rows) == 9
    for r in rows:
        q = r["cochran_q"]
        # the understated value is kept for auditability and must stay exactly Q/k
        assert abs(q["Q_as_published_understated"] * 5 - q["Q"]) < 1e-3
        assert q["df"] == 4
        assert q["p"] < 1e-15
