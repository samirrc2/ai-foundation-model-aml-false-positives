"""Preregistered secondary analysis: is there a COMMON set of missed suspicious cases?

The headline result is a divergence in aggressiveness. The natural follow-up question for a
risk function is the opposite one: do the models fail *together*? If the same suspicious cases
slip past every screener, model diversity buys nothing and the portfolio risk is the single
worst blind spot shared by all of them.

Chance-corrected agreement is the right instrument, and raw agreement is the wrong one. When
misses are rare, two screeners that miss nothing in common still agree on ~90% of cases simply
because both say "caught" almost everywhere. Cohen's kappa divides that inflation out.

Three coefficients are reported because kappa has a known pathology on skewed marginals (the
"kappa paradox": high agreement, low kappa). Scott's pi pools the marginals instead of keeping
them rater-specific, and Gwet's AC1 was designed specifically to be stable under skew. They are
reported together so the conclusion does not rest on the one coefficient most vulnerable to the
shape of this data. The manuscript's claim is the weak one all three support -- agreement is
low -- not a point estimate from any single coefficient.

Computed on the COMMON SUPPORT: the suspicious cases where all five models have a non-NA modal
miss indicator. Restricting to common support is what makes the ten pairwise coefficients
comparable to each other, since a pair evaluated on a different case set is a different
estimand.
"""
from __future__ import annotations
from itertools import combinations

import miss as MI

NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
        "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
        "openai_4o": "GPT-4o"}


def _coefficients(a: list[int], b: list[int]) -> dict[str, float | None]:
    """Cohen's kappa, Scott's pi and Gwet's AC1 for two binary raters on paired items.

    All three share the form (po - pe) / (1 - pe) and differ only in pe:
      Cohen   pe = sum_k p_k(a) * p_k(b)      rater-specific marginals
      Scott   pe = sum_k pbar_k^2            marginals pooled across raters
      Gwet    pe = 2 * pbar_1 * (1 - pbar_1) chance treated as the random half of the pool

    A coefficient is None when its own 1 - pe is zero. That happens when both raters are
    constant and identical (every item the same category): agreement is perfect but there is no
    variance to correct, so the ratio is 0/0 and undefined -- not 1, and not 0. Returning None
    keeps an undefined pair out of the mean instead of silently biasing it.
    """
    n = len(a)
    if n == 0:
        return {"cohen_kappa": None, "scott_pi": None, "gwet_ac1": None, "p_observed": None}
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pbar1 = (pa1 + pb1) / 2

    pe_cohen = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    pe_scott = pbar1 ** 2 + (1 - pbar1) ** 2
    pe_gwet = 2 * pbar1 * (1 - pbar1)

    def _adj(pe):
        return None if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)

    return {"cohen_kappa": _adj(pe_cohen), "scott_pi": _adj(pe_scott),
            "gwet_ac1": _adj(pe_gwet), "p_observed": po}


def run(subgrid_filter: str = "full", allowed_models: set[str] | None = None) -> dict:
    mt = MI.load_miss_table(subgrid_filter=subgrid_filter, allowed_models=allowed_models)
    models = mt.models
    support = mt.common_support(models)
    vec = {m: [mt.miss[m][c] for c in support] for m in models}

    pairs = {}
    for x, y in combinations(models, 2):
        key = f"{NICE.get(x, x)} vs {NICE.get(y, y)}"
        pairs[key] = {k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in _coefficients(vec[x], vec[y]).items()}

    def _stats(name):
        vals = [p[name] for p in pairs.values() if p[name] is not None]
        if not vals:
            return {"mean": None, "min": None, "max": None, "n_defined": 0}
        return {"mean": round(sum(vals) / len(vals), 4), "min": round(min(vals), 4),
                "max": round(max(vals), 4), "n_defined": len(vals)}

    # Cases every model missed. This is the number that would overturn the paper's framing:
    # if it were large, the shared blind spot would matter more than the spread.
    missed_by_all = [c for i, c in enumerate(support)
                     if all(vec[m][i] == 1 for m in models)]
    missed_by_none = [c for i, c in enumerate(support)
                      if all(vec[m][i] == 0 for m in models)]

    per_model = {NICE.get(m, m): {"miss_rate": round(sum(vec[m]) / len(vec[m]), 4),
                                  "n_missed": sum(vec[m])}
                 for m in models} if support else {}
    mr = [v["miss_rate"] for v in per_model.values()]

    return {
        "n_models": len(models),
        "n_suspicious_cases": len(mt.suspicious_cases()),
        "n_common_support": len(support),
        "n_pairs": len(pairs),
        "per_model": per_model,
        "miss_rate_min": round(min(mr), 4) if mr else None,
        "miss_rate_max": round(max(mr), 4) if mr else None,
        "n_missed_by_all_models": len(missed_by_all),
        "n_missed_by_no_model": len(missed_by_none),
        "cohen_kappa": _stats("cohen_kappa"),
        "scott_pi": _stats("scott_pi"),
        "gwet_ac1": _stats("gwet_ac1"),
        # Reported alongside the coefficients because the gap between high raw
        # agreement and low kappa IS the finding to explain, not an inconsistency.
        "raw_agreement": _stats("p_observed"),
        "pairwise": pairs,
    }
