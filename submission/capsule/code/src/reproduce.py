"""Master reproduction entrypoint for the Code Ocean capsule.

Deterministic, offline, $0. Given the frozen battery + frozen capture CSVs, it:
  1. VERIFIES data integrity  — regenerates the battery from its seed and confirms
     the SHA-256 matches the shipped file and the manifest; confirms every capture
     CSV matches its freeze-receipt SHA-256.
  2. RUNS the analysis        — false-positive-variance estimands (altrisk) with
     cluster-bootstrap CIs, the rules + supervised baselines, and the operational
     alert-volume projection.
  3. EMITS results            — pivot_claims.json, baselines.json, alert_volume.json,
     the two manuscript tables (CSV + Markdown), metrics_summary.md, and
     output_hashes.json (for the reproducibility check).

All outputs are timestamp-free so re-runs are byte-identical (see replication_check.py).
"""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import io_paths            # noqa: E402
import loader as C         # noqa: E402
import build_battery as BB  # noqa: E402
import altrisk             # noqa: E402
import baselines           # noqa: E402
import alertvolume as AV   # noqa: E402

DRAWS = 2000
ANALYSIS_SEED = 4242
SUBGRID = "full"


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _write_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True))


# ── 1. data integrity ───────────────────────────────────────────────────────
def verify_data() -> dict:
    cfg = C.load_all()
    checks = {"battery": {}, "capture": {}, "all_ok": True}

    # battery: regenerate deterministically and compare hashes
    manifest = json.loads((io_paths.MANIFEST_DIR / "battery_manifest.json").read_text())
    for which in ("full", "pilot"):
        shipped = io_paths.BATTERY_DIR / f"{which}.jsonl"
        if which == "full":
            cases = BB.mint_full(cfg)
        else:
            cases = BB.subsample_pilot(cfg, BB.mint_full(cfg))
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
            tmp = Path(tf.name)
        regen_hash = BB._write(cases, tmp)
        shipped_hash = _sha256_file(shipped)
        manifest_hash = manifest.get(which, {}).get("sha256")
        ok = (regen_hash == shipped_hash == manifest_hash)
        checks["battery"][which] = {"regenerated_sha256": regen_hash,
                                    "shipped_sha256": shipped_hash,
                                    "manifest_sha256": manifest_hash, "match": ok}
        checks["all_ok"] &= ok
        tmp.unlink(missing_ok=True)

    # capture: each CSV must match its freeze receipt sha256
    for receipt in sorted(io_paths.FROZEN_DIR.glob("*.freeze.json")):
        r = json.loads(receipt.read_text())
        csv_path = io_paths.CAPTURE_DIR / r["csv"]
        actual = _sha256_file(csv_path) if csv_path.exists() else None
        ok = (actual == r["sha256"])
        checks["capture"][r["csv"]] = {"receipt_sha256": r["sha256"],
                                       "actual_sha256": actual, "match": ok,
                                       "n_rows": r.get("n_rows")}
        checks["all_ok"] &= ok
    return checks


# ── 2/3. analysis + emit ────────────────────────────────────────────────────
def _fmt_ci(pair, nd=1, pct=True):
    lo, hi = pair
    if lo is None or hi is None:
        return "n/a"
    f = (lambda x: f"{x*100:.{nd}f}") if pct else (lambda x: f"{x:.{nd}f}")
    return f"[{f(lo)}–{f(hi)}]"


def build_tables(claims, baseline_res, alert_rows, out: Path):
    A = claims["A_false_positive"]
    pm = A["per_model"]
    miss = {m: v["fp_rate"] for m, v in pm.items()}  # placeholder overwrite below

    # per-model miss rates recomputed by altrisk are not in claims; pull from a
    # fresh miss table for the operating-point table.
    import miss as MI
    mt = MI.load_miss_table(subgrid_filter=SUBGRID, allowed_models=set(pm))
    def _missrate(m):
        v = [x for c in mt.suspicious_cases() if (x := mt.miss[m].get(c)) is not None]
        return sum(v) / len(v) if v else None
    NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
            "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
            "openai_4o": "GPT-4o"}

    # Table 1 — operating points
    rows = []
    for m in sorted(pm, key=lambda k: pm[k]["fp_rate"]):
        d = pm[m]; mr = _missrate(m)
        rows.append({"model": NICE.get(m, m), "family": d["family"],
                     "fp_rate": round(d["fp_rate"], 4),
                     "fp_ci95_low": round(d["wilson_ci"][0], 4),
                     "fp_ci95_high": round(d["wilson_ci"][1], 4),
                     "miss_rate": round(mr, 4) if mr is not None else None})
    _write_csv(rows, out / "table1_operating_points.csv")
    md = ["| Model | Family | False-positive rate | Miss rate |",
          "|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['model']} | {r['family']} | {r['fp_rate']*100:.1f}% "
                  f"{_fmt_ci([r['fp_ci95_low'], r['fp_ci95_high']])} | "
                  f"{(r['miss_rate']*100):.1f}% |")
    (out / "table1_operating_points.md").write_text("\n".join(md) + "\n")

    # Table 2 — alert volume
    _write_csv(alert_rows, out / "table2_alert_volume.csv")
    md2 = ["| Screener | FP rate | Daily alerts | False alerts | Precision |",
           "|---|---|---|---|---|"]
    for r in alert_rows:
        md2.append(f"| {r['screener']} | {r['fp_rate']*100:.1f}% | {r['daily_alerts']:,.0f} "
                   f"| {r['false_alerts']:,.0f} | {r['precision']*100:.2f}% |")
    (out / "table2_alert_volume.md").write_text("\n".join(md2) + "\n")


def _write_csv(rows, path: Path):
    import csv
    if not rows:
        path.write_text(""); return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run(verify: bool = True) -> dict:
    out = io_paths.ensure_results()
    summary = {}

    if verify:
        integrity = verify_data()
        _write_json(integrity, out / "data_integrity.json")
        summary["data_integrity_ok"] = integrity["all_ok"]
        if not integrity["all_ok"]:
            raise SystemExit("DATA INTEGRITY FAILURE — see results/data_integrity.json")

    # 2a. FP-variance estimands
    claims = altrisk.analyse(SUBGRID, DRAWS, ANALYSIS_SEED, allow_unfrozen=False)
    _write_json(claims, out / "pivot_claims.json")

    # 2b. baselines
    cases = baselines.load_cases()
    fp_r, miss_r = baselines.run_rules(cases)
    sup = baselines.run_supervised(cases)
    baseline_res = {"rules": {"fp": fp_r, "miss": miss_r},
                    "supervised": {k: {"fp": v[0], "miss": v[1]} for k, v in sup.items()}}
    _write_json(baseline_res, out / "baselines.json")

    # 2c. alert-volume projection
    fp_by_model = {m: d["fp_rate"] for m, d in claims["A_false_positive"]["per_model"].items()}
    NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
            "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
            "openai_4o": "GPT-4o", "rules_baseline": "Rules baseline",
            "supervised_gbm": "Supervised (ceiling)"}
    N, P = 1_000_000, 0.001
    alert_rows = []
    combos = [(m, fp_by_model[m], AV._MISS.get(m, 0.0)) for m in fp_by_model]
    combos += [("rules_baseline", fp_r, miss_r),
               ("supervised_gbm", sup["grad_boost"][0], sup["grad_boost"][1])]
    for m, f, mi in sorted(combos, key=lambda r: r[1]):
        pr = AV.project(f, mi, N, P)
        alert_rows.append({"screener": NICE.get(m, m), "fp_rate": round(f, 4),
                           "daily_alerts": round(pr["daily_alerts"]),
                           "false_alerts": round(pr["false_alerts"]),
                           "precision": round(pr["precision"], 6)})
    _write_json({"N": N, "prevalence": P, "rows": alert_rows}, out / "alert_volume.json")

    # 3. tables + summary
    build_tables(claims, baseline_res, alert_rows, out)
    _write_metrics_summary(claims, baseline_res, alert_rows, out)

    # output hashes (deterministic outputs only)
    hashed = {}
    for name in ("pivot_claims.json", "baselines.json", "alert_volume.json",
                 "table1_operating_points.csv", "table2_alert_volume.csv",
                 "metrics_summary.md"):
        hashed[name] = _sha256_file(out / name)
    _write_json(hashed, out / "output_hashes.json")
    summary["output_hashes"] = hashed
    return summary


def _write_metrics_summary(claims, baseline_res, alert_rows, out: Path):
    A = claims["A_false_positive"]
    lines = ["# Metrics summary — Same Transactions, Different Alarms", "",
             f"Models: {', '.join(claims['meta']['models'])}",
             f"Battery: {claims['meta']['n_benign']} benign / {claims['meta']['n_suspicious']} suspicious | "
             f"error rate {claims['meta']['error_rate']}", "",
             "## Headline (false-positive variance)",
             f"- FP spread (max−min): **{A['fp_spread_pp']*100:.1f} pp** "
             f"({_fmt_ci(A['fp_spread_ci95'])})",
             f"- FP ratio (max/min): ~{A['fp_ratio_maxmin']:.0f}× (secondary; min is a single event)",
             f"- Cross-model disagreement on benign: **{A['divergence_benign']*100:.1f}%** "
             f"({_fmt_ci(A['divergence_benign_ci95'])})", "",
             "## Per-model false-positive rate"]
    for m, d in sorted(A["per_model"].items(), key=lambda kv: kv[1]["fp_rate"]):
        lines.append(f"- {m}: {d['fp_rate']*100:.1f}% {_fmt_ci(d['wilson_ci'])} "
                     f"({d['flags']}/{d['n']})")
    lines += ["", "## Baselines (same battery)",
              f"- Rules (FATF heuristics): FP {baseline_res['rules']['fp']*100:.1f}% / "
              f"miss {baseline_res['rules']['miss']*100:.1f}%",
              f"- Supervised (gradient boosting, out-of-fold): FP "
              f"{baseline_res['supervised']['grad_boost']['fp']*100:.1f}% / "
              f"miss {baseline_res['supervised']['grad_boost']['miss']*100:.1f}%", "",
              "## Operational projection (1,000,000 tx/day @ 0.1% prevalence)"]
    lo = min(r["daily_alerts"] for r in alert_rows if r["screener"] != "Supervised (ceiling)")
    hi = max(r["daily_alerts"] for r in alert_rows)
    lines.append(f"- Daily alert volume across models: {lo:,.0f} → {hi:,.0f} "
                 f"(~{hi/lo:.0f}× on the identical book)")
    lines += ["", "## Supporting",
              f"- Trade-based blind spot (pooled miss): "
              f"{claims['B_typology_miss']['trade_based']['miss_rate']*100:.1f}%",
              f"- Prompt-variant flip: {claims['C_prompt_flip']['flip_rate']*100:.1f}%"]
    (out / "metrics_summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    s = run(verify="--no-verify" not in sys.argv)
    print("[reproduce] data integrity:", s.get("data_integrity_ok"))
    print("[reproduce] wrote results/ (pivot_claims.json, baselines.json, "
          "alert_volume.json, tables, metrics_summary.md)")
