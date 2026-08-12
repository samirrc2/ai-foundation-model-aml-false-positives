"""Formal hypothesis tests (P-values) + publication figures for the Scientific
Reports submission. Deterministic, $0. Reads the frozen capture CSVs.

Tests (models screen the SAME cases -> paired/related binary design):
  - Overall difference in false-positive rate across the 5 models: Cochran's Q
    (k related binary samples), df = k-1, exact-ish chi-square P.
  - Pairwise: McNemar exact (binomial) on discordant benign cases, Bonferroni
    over the 10 model pairs.

Figures (vector PDF + PNG, 300 dpi, sans-serif, untruncated axes, 95% CI bars):
  1 per-model false-positive rate (Wilson 95% CI)
  2 operating points: sensitivity vs false-positive rate (models + baselines)
  3 projected daily alert volume at 0.1% prevalence (log scale)
  4 per-typology miss rate (Wilson 95% CI) — the trade-based blind spot
"""
from __future__ import annotations
import csv, glob, json, math, os
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

_HERE = Path(__file__).resolve().parent
_RAW = _HERE.parent / "data" / "raw"
_OUT = _HERE.parent / "paper_scireports"
_FIG = _OUT / "figures"
NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
        "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
        "openai_4o": "GPT-4o"}
ORDER = ["gemini_flash", "openai_4o", "openai_41_mini", "gemini_flash_lite", "openai_4o_mini"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0, c - h), min(1, c + h))


def load():
    rows = []
    for f in glob.glob(str(_RAW / "runs_full_*.csv")):
        if os.path.getsize(f) == 0 or "xai_grok" in f:
            continue
        for r in csv.DictReader(open(f)):
            if r.get("mode") == "REAL":
                rows.append(r)
    return rows


def modal(v):
    return 1 if sum(v) > len(v) / 2 else 0


def per_case(rows, label):
    """model -> case_id -> modal flag(1)/no(0) for the given label."""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["label"] != label or r["decision"] == "ERROR":
            continue
        acc[r["model_key"]][r["case_id"]].append(1 if r["decision"] == "flag" else 0)
    return {m: {c: modal(v) for c, v in d.items()} for m, d in acc.items()}


def cochran_q(mat):
    """mat: list of rows (cases) x k columns (models), binary. Returns Q, df, p."""
    k = len(mat[0]); N = len(mat)
    Cj = [sum(row[j] for row in mat) for j in range(k)]
    Ri = [sum(row) for row in mat]
    Cbar = sum(Cj) / k
    num = (k - 1) * sum((c - Cbar) ** 2 for c in Cj)
    den = k * sum(Ri) - sum(r * r for r in Ri)
    Q = num / den if den else 0.0
    df = k - 1
    p = 1 - stats.chi2.cdf(Q, df)
    return Q, df, p


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(stats.binom.pmf(i, n, 0.5) for i in range(0, k + 1))
    return min(1.0, p)


def main():
    _FIG.mkdir(parents=True, exist_ok=True)
    rows = load()
    fpc = per_case(rows, "benign")
    misc_raw = per_case(rows, "suspicious")            # flag=1 -> caught; miss = 1-flag
    models = [m for m in ORDER if m in fpc]
    cases = sorted(set.intersection(*[set(fpc[m]) for m in models]))

    # ---- overall Cochran's Q on benign false positives ----
    mat = [[fpc[m][c] for m in models] for c in cases]
    Q, df, pq = cochran_q(mat)

    # ---- per-model FP + miss with Wilson CI ----
    per_model = {}
    for m in models:
        fk = sum(fpc[m][c] for c in cases); fn = len(cases)
        scases = sorted(misc_raw[m]); mk = sum(1 - misc_raw[m][c] for c in scases); mn = len(scases)
        per_model[m] = {"fp": fk / fn, "fp_ci": wilson(fk, fn), "fp_k": fk, "fp_n": fn,
                        "miss": mk / mn, "miss_ci": wilson(mk, mn)}

    # ---- pairwise McNemar exact, Bonferroni ----
    pairs = {}
    m_pairs = list(combinations(models, 2))
    for a, b in m_pairs:
        bb = sum(1 for c in cases if fpc[a][c] == 1 and fpc[b][c] == 0)
        cc = sum(1 for c in cases if fpc[a][c] == 0 and fpc[b][c] == 1)
        p = mcnemar_exact(bb, cc)
        pairs[f"{NICE[a]} vs {NICE[b]}"] = {"b": bb, "c": cc, "p_exact": p,
                                            "p_bonferroni": min(1.0, p * len(m_pairs))}

    # ---- per-typology miss ----
    casetyp = {r["case_id"]: r["typology"] for r in rows if r["label"] == "suspicious"}
    typ = defaultdict(lambda: [0, 0])
    for m in models:
        for c, fl in misc_raw[m].items():
            t = casetyp.get(c)
            if t:
                typ[t][1] += 1; typ[t][0] += (1 - fl)
    typ_stats = {t: {"miss": k / n, "ci": wilson(k, n), "k": k, "n": n}
                 for t, (k, n) in typ.items()}

    tests = {"cochran_q": {"Q": Q, "df": df, "p": pq, "n_cases": len(cases), "k_models": len(models)},
             "pairwise_mcnemar": pairs,
             "per_model": {NICE[m]: per_model[m] for m in models},
             "per_typology_miss": typ_stats}
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / "stats_tests.json").write_text(json.dumps(tests, indent=2, sort_keys=True, default=float))

    # ============================ FIGURES ============================
    def _save(fig, name):
        fig.savefig(_FIG / f"{name}.pdf", bbox_inches="tight")
        fig.savefig(_FIG / f"{name}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    # Fig 1 — per-model FP rate with 95% CI
    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    xs = range(len(models))
    fps = [per_model[m]["fp"] * 100 for m in models]
    err = [[(per_model[m]["fp"] - per_model[m]["fp_ci"][0]) * 100 for m in models],
           [(per_model[m]["fp_ci"][1] - per_model[m]["fp"]) * 100 for m in models]]
    ax.bar(xs, fps, yerr=err, capsize=4, color="#4C72B0", edgecolor="black", linewidth=0.6)
    ax.set_xticks(list(xs)); ax.set_xticklabels([NICE[m] for m in models], rotation=20, ha="right")
    ax.set_ylabel("False-positive rate (%)"); ax.set_ylim(0, 100)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _save(fig, "fig1_fp_by_model")

    # Fig 2 — operating points (sensitivity vs FP), models + baselines
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    for m in models:
        x = per_model[m]["fp"] * 100; y = (1 - per_model[m]["miss"]) * 100
        ax.scatter(x, y, s=55, color="#4C72B0", edgecolor="black", zorder=3)
        ax.annotate(NICE[m], (x, y), textcoords="offset points", xytext=(6, -3), fontsize=8)
    # baselines
    for name, (fp, miss), col in [("Rules", (0.12, 0.113), "#C44E52"),
                                  ("Supervised", (0.0, 0.0), "#55A868")]:
        ax.scatter(fp * 100, (1 - miss) * 100, s=55, marker="^", color=col,
                   edgecolor="black", zorder=3)
        ax.annotate(name, (fp * 100, (1 - miss) * 100), textcoords="offset points",
                    xytext=(6, -3), fontsize=8)
    ax.set_xlabel("False-positive rate (%)"); ax.set_ylabel("Sensitivity (% suspicious caught)")
    ax.set_xlim(-3, 100); ax.set_ylim(80, 101)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _save(fig, "fig2_operating_points")

    # Fig 3 — projected daily alert volume @ 0.1% prevalence (log scale)
    N, p = 1_000_000, 0.001
    def alerts(fp, miss):
        return fp * N * (1 - p) + (1 - miss) * N * p
    scr = [(NICE[m], per_model[m]["fp"], per_model[m]["miss"]) for m in models]
    scr += [("Rules", 0.12, 0.113), ("Supervised", 0.0, 0.0)]
    scr.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    vals = [alerts(fp, mi) for _n, fp, mi in scr]
    cols = ["#55A868" if n == "Supervised" else ("#C44E52" if n == "Rules" else "#4C72B0")
            for n, _f, _m in scr]
    ax.bar(range(len(scr)), vals, color=cols, edgecolor="black", linewidth=0.6)
    ax.set_yscale("log")
    ax.set_xticks(range(len(scr))); ax.set_xticklabels([n for n, _f, _m in scr], rotation=25, ha="right")
    ax.set_ylabel("Projected daily alerts (log scale)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _save(fig, "fig3_alert_volume")

    # Fig 4 — per-typology miss with CI
    tp = sorted(typ_stats, key=lambda t: -typ_stats[t]["miss"])
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ys = [typ_stats[t]["miss"] * 100 for t in tp]
    err = [[(typ_stats[t]["miss"] - typ_stats[t]["ci"][0]) * 100 for t in tp],
           [(typ_stats[t]["ci"][1] - typ_stats[t]["miss"]) * 100 for t in tp]]
    ax.bar(range(len(tp)), ys, yerr=err, capsize=3, color="#8172B3", edgecolor="black", linewidth=0.6)
    ax.set_xticks(range(len(tp))); ax.set_xticklabels([t.replace("_", " ") for t in tp],
                                                      rotation=30, ha="right")
    ax.set_ylabel("Miss rate (%, pooled over models)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _save(fig, "fig4_typology_miss")

    print(f"[figures_stats] Cochran Q={Q:.1f} df={df} p={pq:.2e} (n={len(cases)} benign cases, k={len(models)})")
    print("[figures_stats] pairwise McNemar (Bonferroni p):")
    for k, v in pairs.items():
        print(f"    {k:34s} b={v['b']:3d} c={v['c']:3d} p_bonf={v['p_bonferroni']:.2e}")
    print(f"[figures_stats] wrote 4 figures (pdf+png) + stats_tests.json to {_OUT}")


if __name__ == "__main__":
    main()
