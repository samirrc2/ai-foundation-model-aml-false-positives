"""Base-rate translation: project balanced-battery false-positive/miss rates to
operational alert volume and precision at a realistic suspicious prevalence. Turns
the SAR-burden argument from rhetoric into numbers. Pure, $0.

At prevalence p over N daily transactions: legitimate ~ N(1-p), suspicious ~ Np.
  daily alerts   = FP*N(1-p) + (1-miss)*Np
  false alerts   = FP*N(1-p)
  true alerts    = (1-miss)*Np
  precision      = true / (true + false)     (share of alerts that are real)
Alert volume is FP-dominated at low p, so model choice ~ multiplies the alert queue.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CLAIMS = _HERE.parent / "pivot_claims.json"

# per-model miss rates (full battery, computed alongside FP) + baselines
_MISS = {"gemini_flash": 0.120, "openai_4o": 0.033, "openai_41_mini": 0.037,
         "gemini_flash_lite": 0.007, "openai_4o_mini": 0.000}
_BASELINES = {"rules_baseline": (0.120, 0.113), "supervised_gbm": (0.000, 0.000)}


def project(fp, miss, N=1_000_000, p=0.001):
    legit, susp = N * (1 - p), N * p
    false_a = fp * legit
    true_a = (1 - miss) * susp
    alerts = false_a + true_a
    prec = true_a / alerts if alerts else 0.0
    return {"daily_alerts": alerts, "false_alerts": false_a, "true_alerts": true_a,
            "precision": prec}


def main():
    N = 1_000_000
    p = 0.001
    fp = {}
    if _CLAIMS.exists():
        c = json.loads(_CLAIMS.read_text())
        fp = {m: d["fp_rate"] for m, d in c["A_false_positive"]["per_model"].items()}
    print(f"[alertvolume] N={N:,} transactions/day, suspicious prevalence p={p:.1%}\n")
    print(f"  {'model / baseline':22s} {'FP':>6s} {'daily alerts':>13s} "
          f"{'false alerts':>13s} {'precision':>10s}")
    rows = [(m, fp[m], _MISS.get(m, 0.0)) for m in fp]
    rows += [(m, f, mi) for m, (f, mi) in _BASELINES.items()]
    rows.sort(key=lambda r: r[1])
    vols = {}
    for m, f, mi in rows:
        r = project(f, mi, N, p)
        vols[m] = r["daily_alerts"]
        print(f"  {m:22s} {f:6.1%} {r['daily_alerts']:13,.0f} "
              f"{r['false_alerts']:13,.0f} {r['precision']:10.2%}")
    lo, hi = min(vols.values()), max(vols.values())
    print(f"\n  alert-volume swing across models: {lo:,.0f} -> {hi:,.0f} "
          f"= {hi/lo:.0f}x on the IDENTICAL book.")
    print(f"  worst LLM (gpt-4o-mini) vs legacy rules: "
          f"{vols['openai_4o_mini']/vols['rules_baseline']:.1f}x the alert queue.")


if __name__ == "__main__":
    sys.exit(main())
