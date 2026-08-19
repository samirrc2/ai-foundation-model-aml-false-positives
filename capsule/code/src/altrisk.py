"""Pivot analysis — "AI foundation model choice and false positive variation in Anti Money Laundering transaction screening" (model-risk audit of LLM
AML screening). Pure, $0, reads FROZEN CSVs only. Emits pivot_claims.json with the
Candidate-A/B/C estimands, each with a cluster-bootstrap CI over strata.

A (headline): per-model FALSE-POSITIVE rate on benign hard-negatives; the
             cross-model FP spread (max/min, ratio) and cross-model DIVERGENCE.
B (support): per-FATF-typology miss rate (the trade-based blind spot).
C (support): prompt-variant decision-flip rate.

STATUS: these are the CONFIRMATORY numbers from the pre-registered full run over
the five foundation models. The estimands (A/B/C) and the modal-vote tie rule
(ties resolve to flag) were fixed in advance; see docs/PREREGISTRATION.md and
docs/DECISIONS.md. The status is echoed into pivot_claims.json.
"""
from __future__ import annotations
import argparse, csv, json, sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import io_paths            # noqa: E402
import miss as MI          # noqa: E402  (frozen-CSV loader + MissTable)
import stats as S          # noqa: E402
import loader as C         # noqa: E402

_HERE = Path(__file__).resolve().parent
_RAW = io_paths.CAPTURE_DIR
_OUT = io_paths.RESULTS_DIR / "pivot_claims.json"


def _load_real_rows(subgrid: str, allowed: set[str]) -> list[dict]:
    rows = []
    for p in sorted(_RAW.glob(f"runs_{subgrid}_*.csv")):
        if p.stat().st_size == 0:
            continue
        with p.open() as f:
            r0 = next(csv.DictReader(f), None)
        if not r0 or r0["model_key"] not in allowed:
            continue
        for r in csv.DictReader(p.open()):
            rows.append(r)
    return rows


def _modal(vals: list[int]) -> int:
    return 1 if sum(vals) > len(vals) / 2 else 0


# ── Candidate A: false-positive rate + spread + divergence ───────────────────
def fp_rates(mt: MI.MissTable) -> dict:
    benign = mt.benign_cases()
    out = {}
    for m in mt.models:
        v = [x for c in benign if (x := mt.flag_benign[m].get(c)) is not None]
        k, n = sum(v), len(v)
        lo, hi = S.wilson_ci(k, n)
        out[m] = {"family": mt.family[m], "fp_rate": (k / n if n else None),
                  "flags": k, "n": n, "wilson_ci": [lo, hi]}
    return out


def _fp_rate_on(mt, model, cases):
    v = [x for c in cases if (x := mt.flag_benign[model].get(c)) is not None]
    return (sum(v) / len(v)) if v else None


def fp_spread(mt: MI.MissTable, cases: list[str]) -> float | None:
    rates = [r for m in mt.models if (r := _fp_rate_on(mt, m, cases)) is not None]
    if len(rates) < 2:
        return None
    return max(rates) - min(rates)          # additive spread (pp)


def fp_ratio(mt: MI.MissTable, cases: list[str]) -> float | None:
    rates = [r for m in mt.models if (r := _fp_rate_on(mt, m, cases)) is not None]
    rates = [r for r in rates if r is not None]
    lo = min(rates) if rates else None
    hi = max(rates) if rates else None
    if not rates or lo <= 0:
        return None
    return hi / lo


def divergence(mt: MI.MissTable, cases: list[str], which: str) -> float | None:
    """Fraction of `cases` on which the models' modal flag decisions are not
    unanimous. which='benign' uses flag_benign; 'suspicious' uses miss->flag."""
    n = dis = 0
    for c in cases:
        if which == "benign":
            decs = [mt.flag_benign[m].get(c) for m in mt.models]
        else:
            decs = [None if mt.miss[m].get(c) is None else (0 if mt.miss[m][c] == 1 else 1)
                    for m in mt.models]
        decs = [d for d in decs if d is not None]
        if len(decs) < len(mt.models):
            continue
        n += 1
        dis += (len(set(decs)) > 1)
    return (dis / n) if n else None


# ── Candidate B: per-typology miss ───────────────────────────────────────────
def typology_miss(mt: MI.MissTable) -> dict:
    by = defaultdict(lambda: [0, 0])
    for c in mt.suspicious_cases():
        typ = mt.cases_meta[c]["typology"]
        for m in mt.models:
            x = mt.miss[m].get(c)
            if x is None:
                continue
            by[typ][1] += 1
            by[typ][0] += x
    out = {}
    for typ, (k, n) in by.items():
        lo, hi = S.wilson_ci(k, n)
        out[typ] = {"miss_rate": (k / n if n else None), "misses": k, "n": n,
                    "wilson_ci": [lo, hi]}
    return dict(sorted(out.items(), key=lambda kv: -(kv[1]["miss_rate"] or 0)))


# ── Candidate C: prompt-variant flip ─────────────────────────────────────────
def prompt_flip(rows: list[dict]) -> dict:
    by = defaultdict(dict)   # (model,case,seed) -> variant -> decision
    for r in rows:
        if r["decision"] == "ERROR":
            continue
        by[(r["model_key"], r["case_id"], r["seed_index"])][r["prompt_variant"]] = r["decision"]
    flip = tot = 0
    variants = sorted({r["prompt_variant"] for r in rows})
    for _k, d in by.items():
        if len(d) >= 2:
            vals = list(d.values())
            tot += 1
            flip += (len(set(vals)) > 1)
    lo, hi = S.wilson_ci(flip, tot)
    return {"flip_rate": (flip / tot if tot else None), "flips": flip, "n_pairs": tot,
            "variants": variants, "wilson_ci": [lo, hi]}


def analyse(subgrid: str, draws: int, seed: int, allow_unfrozen: bool) -> dict:
    cfg = C.load_all()
    allowed = set(C.subgrid(cfg, subgrid).models)
    mt = MI.load_miss_table(subgrid_filter=subgrid, allow_unfrozen=allow_unfrozen,
                            allowed_models=allowed)
    rows = _load_real_rows(subgrid, allowed)
    benign = mt.benign_cases()
    allcases = mt.suspicious_cases() + benign

    fp = fp_rates(mt)
    spread_ci = S.cluster_bootstrap(mt, benign, lambda cs: fp_spread(mt, cs), draws, seed)
    ratio_ci = S.cluster_bootstrap(mt, benign, lambda cs: fp_ratio(mt, cs), draws, seed)
    div_benign_ci = S.cluster_bootstrap(mt, benign, lambda cs: divergence(mt, cs, "benign"),
                                        draws, seed)

    rates = [fp[m]["fp_rate"] for m in mt.models if fp[m]["fp_rate"] is not None]
    return {
        "meta": {
            "paper": "AI foundation model choice and false positive variation in Anti "
                     "Money Laundering transaction screening",
            "status": "CONFIRMATORY: pre-registered full run over the five foundation "
                      "models (see docs/PREREGISTRATION.md and docs/DECISIONS.md)",
            "subgrid": subgrid, "mode": mt.mode, "config_hash": cfg.config_hash(),
            "models": mt.models, "families": {m: mt.family[m] for m in mt.models},
            "n_benign": len(benign), "n_suspicious": len(mt.suspicious_cases()),
            "n_rows": mt.n_rows, "error_rate": round(MI.error_rate(mt), 4),
            "analysis_seed": seed, "bootstrap_draws": draws,
        },
        "A_false_positive": {
            "per_model": fp,
            "fp_rate_min": (min(rates) if rates else None),
            "fp_rate_max": (max(rates) if rates else None),
            "fp_spread_pp": spread_ci["point"], "fp_spread_ci95": [spread_ci["ci_low"], spread_ci["ci_high"]],
            "fp_ratio_maxmin": ratio_ci["point"], "fp_ratio_ci95": [ratio_ci["ci_low"], ratio_ci["ci_high"]],
            "divergence_benign": div_benign_ci["point"],
            "divergence_benign_ci95": [div_benign_ci["ci_low"], div_benign_ci["ci_high"]],
        },
        "B_typology_miss": typology_miss(mt),
        "C_prompt_flip": prompt_flip(rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subgrid", default="pilot")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--allow-unfrozen", action="store_true")
    ap.add_argument("--out", default=str(_OUT))
    args = ap.parse_args()
    claims = analyse(args.subgrid, args.draws, args.seed, args.allow_unfrozen)
    Path(args.out).write_text(json.dumps(claims, indent=2, sort_keys=True))
    A = claims["A_false_positive"]
    print(f"[altrisk] mode={claims['meta']['mode']} models={len(claims['meta']['models'])}")
    print("[altrisk] A — per-model false-positive rate:")
    for m, d in A["per_model"].items():
        lo, hi = d["wilson_ci"]
        print(f"    {m:20s} FP={d['fp_rate']:.1%}  ({d['flags']}/{d['n']})  CI[{lo:.1%},{hi:.1%}]")
    print(f"[altrisk] A — FP spread={A['fp_spread_pp']:.1%} pp  CI{[round(x,3) for x in A['fp_spread_ci95']]} | "
          f"ratio(max/min)={A['fp_ratio_maxmin']}  | benign divergence={A['divergence_benign']:.1%}")
    print("[altrisk] B — per-typology miss (top 3):")
    for t, d in list(claims["B_typology_miss"].items())[:3]:
        print(f"    {t:20s} miss={d['miss_rate']:.1%} ({d['misses']}/{d['n']})")
    print(f"[altrisk] C — prompt-flip={claims['C_prompt_flip']['flip_rate']:.1%} "
          f"({claims['C_prompt_flip']['flips']}/{claims['C_prompt_flip']['n_pairs']}) -> pivot_claims.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
