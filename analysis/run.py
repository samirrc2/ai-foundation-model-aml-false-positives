"""SINGLE analysis entrypoint — pure, deterministic, $0. Reads frozen capture CSVs
and emits claims.json: every number the paper will cite, each with its CI and the
config/battery hash that produced it. Also computes the three pilot-gate booleans.

  python analysis/run.py --subgrid pilot [--draws 2000] [--seed 4242] [--allow-unfrozen]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))

import miss as MI            # noqa: E402
import correlation as X      # noqa: E402
import defense as D          # noqa: E402
import stats as S            # noqa: E402
import loader as C           # noqa: E402

_HERE = Path(__file__).resolve().parent
_MANI = _HERE.parent / "manifest"
_OUT = _HERE.parent / "claims.json"


def _read_ledger(subgrid: str) -> dict:
    for mode in ("REAL", "MOCK"):
        p = _MANI / f"ledger_{subgrid}_{mode}.json"
        if p.exists() and p.stat().st_size > 0:
            try:
                d = json.loads(p.read_text())
                return {"mode": mode, "cum_usd": d.get("cum_usd", 0.0),
                        "per_model": d.get("per_model", {})}
            except ValueError:
                pass
    return {"mode": None, "cum_usd": 0.0, "per_model": {}}


def _battery_hash() -> dict:
    p = _MANI / "battery_manifest.json"
    if p.exists():
        d = json.loads(p.read_text())
        return {k: d[k]["sha256"] for k in ("pilot", "full") if k in d}
    return {}


def analyse(subgrid: str, draws: int, seed: int, allow_unfrozen: bool) -> dict:
    cfg0 = C.load_all()
    allowed = set(C.subgrid(cfg0, subgrid).models)
    mt = MI.load_miss_table(subgrid_filter=subgrid, allow_unfrozen=allow_unfrozen,
                            allowed_models=allowed)
    models = mt.models
    susp = mt.suspicious_cases()
    support = mt.common_support(models)          # suspicious cases scored by all models
    cfg = C.load_all()
    ledger = _read_ledger(subgrid)

    # ── marginals (pooled + per model, Wilson CI) ────────────────────────────
    per_model = {}
    pooled_k = pooled_n = 0
    for m in models:
        v = [x for c in support if (x := mt.miss[m].get(c)) is not None]
        k, n = sum(v), len(v)
        lo, hi = S.wilson_ci(k, n)
        per_model[m] = {"family": mt.family[m], "miss_rate": (k / n if n else None),
                        "n": n, "misses": k, "wilson_ci": [lo, hi],
                        "miss_upper95": hi,
                        "rule_of_three_upper": (3.0 / n if (k == 0 and n) else None)}
        pooled_k += k; pooled_n += n
    pooled_miss = pooled_k / pooled_n if pooled_n else None

    # ── miss-rate upper bound: a clean/near-zero sweep is a BOUND, not a shrug ──
    #    (Amendment A3.) Reported so a second KILL is a quantified finding.
    pooled_upper = S.wilson_ci(pooled_k, pooled_n)[1] if pooled_n else None
    miss_bounds = {
        "pooled_misses": pooled_k, "pooled_n": pooled_n,
        "pooled_miss_upper95_wilson": pooled_upper,
        "pooled_rule_of_three_upper": (3.0 / pooled_n if (pooled_k == 0 and pooled_n) else None),
        "per_model": {m: {"misses": per_model[m]["misses"], "n": per_model[m]["n"],
                          "miss_upper95": per_model[m]["miss_upper95"],
                          "rule_of_three_upper": per_model[m]["rule_of_three_upper"]}
                      for m in models},
        "correlation_feasibility_note": (
            "Measuring miss-correlation needs misses in quantity. If the per-model "
            "miss rate is bounded near a few percent, joint misses are rarer still "
            "and estimating the joint-miss ratio with a usable CI is unaffordable "
            "under BUDGET_FULL -> feasibility falsification (Amendment A3)."),
    }

    # ── primary: joint-miss ratio (full set) with cluster-bootstrap CI ───────
    jm = X.joint_miss(mt, models, support)
    ratio_fn = lambda cs: X.joint_miss(mt, models, cs)["ratio"]          # noqa: E731
    ratio_ci = S.cluster_bootstrap(mt, support, ratio_fn, draws=draws, seed=seed)
    jobs_ci = S.cluster_bootstrap(mt, support, lambda cs: X.joint_miss(mt, models, cs)["j_obs"],
                                  draws=draws, seed=seed)

    # ── pairwise agreement matrices (κ headline; π, AC1 robustness) ──────────
    matrices = {s: X.pairwise_matrix(mt, models, support, stat=s)
                for s in ("kappa", "scott_pi", "gwet_ac1")}

    # ── within vs cross family contrast (κ) + CI on the contrast ─────────────
    contrast = X.within_cross_contrast(mt, models, support, stat="kappa")
    contrast_ci = S.cluster_bootstrap(
        mt, support,
        lambda cs: X.within_cross_contrast(mt, models, cs, stat="kappa")["contrast"],
        draws=draws, seed=seed)

    # ── defense-in-depth recovery ────────────────────────────────────────────
    defense = D.summary(mt, models, support)
    het_ci = S.cluster_bootstrap(mt, support, lambda cs: D.het_recovery_scalar(mt, models, cs),
                                 draws=draws, seed=seed)

    # ── robustness: prevalence/churn + per-variant ratio ─────────────────────
    pc = X.prevalence_churn(mt, models, support)
    per_variant = {}
    for v in sorted(mt.variants):
        # recompute a miss table filtered to a single variant would need re-load;
        # approximate per-variant signal is reported at full aggregation (variants
        # already pooled into the modal vote). We expose the variant list for audit.
        per_variant[v] = "pooled into modal vote (see PREREGISTRATION §6)"

    # ── pilot gate ───────────────────────────────────────────────────────────
    err = MI.error_rate(mt)
    cap = float(getattr(cfg.grid.budgets, subgrid, cfg.grid.budgets.pilot))
    ran_clean = (err <= 0.02) and (ledger["cum_usd"] <= cap)
    base_in_band = (pooled_miss is not None) and (0.10 <= pooled_miss <= 0.70)
    signal = (jm["ratio"] is not None and jm["ratio"] > 1.0
              and ratio_ci["ci_low"] is not None and ratio_ci["ci_high"] is not None)
    contrast_computable = contrast["contrast"] is not None

    claims = {
        "meta": {
            "subgrid": subgrid, "mode": mt.mode, "config_hash": cfg.config_hash(),
            "battery_sha256": _battery_hash(), "analysis_seed": seed, "bootstrap_draws": draws,
            "models": models, "families": {m: mt.family[m] for m in models},
            "prompt_variants": sorted(mt.variants), "seed_indices": sorted(mt.seed_indices),
            "n_rows": mt.n_rows, "n_error": mt.n_error, "error_rate": round(err, 4),
            "n_suspicious_cases": len(susp), "n_common_support": len(support),
            "spend_usd": ledger["cum_usd"], "budget_cap_usd": cap,
        },
        "primary_joint_miss": {
            "j_observed": jm["j_obs"], "j_independence": jm["j_ind"],
            "ratio": jm["ratio"], "ratio_ci95": [ratio_ci["ci_low"], ratio_ci["ci_high"]],
            "j_observed_ci95": [jobs_ci["ci_low"], jobs_ci["ci_high"]],
            "ci_excludes_1": S.ci_excludes(ratio_ci, 1.0, "above"),
            "n_strata": ratio_ci["n_strata"],
        },
        "systemic_failure_ratio": {
            "value": X.systemic_failure_ratio(mt, models, support),
            "note": "Bommasani homogenization metric (== primary ratio for the full set)",
        },
        "marginal_miss_rates": {"pooled": pooled_miss, "per_model": per_model},
        "miss_rate_bounds": miss_bounds,
        "pairwise_agreement_on_misses": {
            "kappa_matrix": matrices["kappa"], "scott_pi_matrix": matrices["scott_pi"],
            "gwet_ac1_matrix": matrices["gwet_ac1"],
        },
        "within_vs_cross_family": {
            **contrast,
            "contrast_ci95": [contrast_ci["ci_low"], contrast_ci["ci_high"]],
        },
        "defense_in_depth": {
            "heterogeneous_recovery_mean": defense["heterogeneous_recovery_mean"],
            "heterogeneous_recovery_ci95": [het_ci["ci_low"], het_ci["ci_high"]],
            "homogeneous_recovery_mean": defense["homogeneous_recovery_mean"],
            "n_heterogeneous_pairs": defense["n_heterogeneous_pairs"],
            "n_homogeneous_pairs": defense["n_homogeneous_pairs"],
            "recovery_below_1": S.ci_excludes(het_ci, 1.0, "below"),
            "pairs": defense["pairs"],
        },
        "robustness": {"prevalence_churn": pc, "per_variant": per_variant},
        "pilot_gate": {
            "criterion_1_ran_clean": ran_clean,
            "criterion_2_base_rate_in_band": base_in_band,
            "criterion_3_signal": signal,
            "criterion_3_contrast_computable": contrast_computable,
            "pooled_miss_rate": pooled_miss, "error_rate": round(err, 4),
            "spend_usd": ledger["cum_usd"], "joint_miss_ratio": jm["ratio"],
        },
    }
    return claims


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subgrid", default="pilot")
    ap.add_argument("--draws", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--allow-unfrozen", action="store_true")
    ap.add_argument("--out", default=str(_OUT))
    args = ap.parse_args()
    cfg = C.load_all()
    draws = args.draws if args.draws is not None else 2000
    seed = args.seed if args.seed is not None else int(cfg.grid.analysis_seed)
    claims = analyse(args.subgrid, draws, seed, args.allow_unfrozen)
    Path(args.out).write_text(json.dumps(claims, indent=2, sort_keys=True))
    g = claims["pilot_gate"]

    def _f(x, nd=3):
        return f"{x:.{nd}f}" if isinstance(x, (int, float)) else "n/a"
    print(f"[analysis] mode={claims['meta']['mode']} models={len(claims['meta']['models'])} "
          f"support={claims['meta']['n_common_support']} err={claims['meta']['error_rate']}")
    print(f"[analysis] pooled miss={_f(g['pooled_miss_rate'])} | joint ratio="
          f"{_f(claims['primary_joint_miss']['ratio'], 2)} "
          f"CI{claims['primary_joint_miss']['ratio_ci95']} | "
          f"het recovery={_f(claims['defense_in_depth']['heterogeneous_recovery_mean'])}")
    print(f"[analysis] pilot gate: clean={g['criterion_1_ran_clean']} "
          f"band={g['criterion_2_base_rate_in_band']} signal={g['criterion_3_signal']} "
          f"-> claims.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
