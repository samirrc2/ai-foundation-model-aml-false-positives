"""EXTENSION analysis for the Discover Artificial Intelligence retarget.

Pure, $0, reads the FROZEN capture CSVs only (data/raw/runs_full_*.csv). NO API calls.
Standardises the modal-vote tie rule on **ties -> flag** (preregistered, DECISIONS D4)
across BOTH tables and figures, fixing the table/figure inconsistency where
figures_stats.py used ties -> miss.

Emits to OUTDIR:
  classification_metrics.{json,csv,md}   per-model prec/rec/spec/F1/BalAcc/MCC/Acc/NPV + Wilson CIs
  stats_tests_corrected.json             Cochran Q + McNemar (FP, unchanged) + per-model & per-typology (ties->flag)
  prompt_sensitivity.{json,csv}          per-model FP under each prompt variant
  figures/fig1..fig7 (pdf+png)           corrected + new display items
"""
from __future__ import annotations
import csv, glob, os, math, json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "raw"
OUT = Path(os.environ.get("OUTDIR", "/mnt/user-data/outputs/p4_ext"))
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
        "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
        "openai_4o": "GPT-4o"}
FAM = {"gemini_flash": "Google", "gemini_flash_lite": "Google", "openai_4o": "OpenAI",
       "openai_41_mini": "OpenAI", "openai_4o_mini": "OpenAI"}
# display order: cautious -> flooding (matches manuscript Table 1)
ORDER = ["gemini_flash", "openai_4o", "openai_41_mini", "gemini_flash_lite", "openai_4o_mini"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
BLUE, RED, GREEN, PURPLE = "#4C72B0", "#C44E52", "#55A868", "#8172B3"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load():
    rows = []
    for f in glob.glob(str(RAW / "runs_full_*.csv")):
        if os.path.getsize(f) == 0 or "xai_grok" in f:
            continue
        for r in csv.DictReader(open(f)):
            if r.get("mode") == "REAL":
                rows.append(r)
    return rows


def modal_flag(v):
    """Benign FP rule: flag iff STRICT majority flagged; a 2/2 tie -> NOT flagged
    (miss.py _modal(want='flag'); ties never over-count FPs)."""
    return 1 if sum(v) > len(v) / 2 else 0


def modal_caught(v):
    """Suspicious rule: a case is MISSED iff STRICT majority said no_flag
    (miss.py _modal(want='no_flag')); a 2/2 tie -> NOT a miss = caught. So caught
    iff flags >= half. This is the preregistered ties->flag rule (D4)."""
    return 1 if 2 * sum(v) >= len(v) else 0


def per_case(rows, label, seed_filter=None, variant_filter=None):
    rule = modal_caught if label == "suspicious" else modal_flag
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["label"] != label or r["decision"] == "ERROR":
            continue
        if seed_filter is not None and r["seed_index"] != seed_filter:
            continue
        if variant_filter is not None and r["prompt_variant"] != variant_filter:
            continue
        acc[r["model_key"]][r["case_id"]].append(1 if r["decision"] == "flag" else 0)
    return {m: {c: rule(v) for c, v in d.items()} for m, d in acc.items()}


def cochran_q(mat):
    k = len(mat[0]); Cj = [sum(row[j] for row in mat) for j in range(k)]
    Ri = [sum(row) for row in mat]; Cbar = sum(Cj) / k
    num = (k - 1) * sum((c - Cbar) ** 2 for c in Cj)
    den = k * sum(Ri) - sum(r * r for r in Ri)
    Q = num / den if den else 0.0
    return Q, k - 1, 1 - stats.chi2.cdf(Q, k - 1)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(stats.binom.pmf(i, n, 0.5) for i in range(k + 1)))


def main():
    rows = load()
    fpc = per_case(rows, "benign")          # model -> case -> modal flag (canonical)
    catch = per_case(rows, "suspicious")    # model -> case -> modal flag; miss = 1 - flag
    models = [m for m in ORDER if m in fpc]
    bcases = sorted(set.intersection(*[set(fpc[m]) for m in models]))
    scases = sorted(set.intersection(*[set(catch[m]) for m in models]))
    casetyp = {r["case_id"]: r["typology"] for r in rows if r["label"] == "suspicious"}

    # ---------- per-model full classification metrics (ties->flag) ----------
    per_model = {}
    for m in models:
        TP = sum(catch[m][c] for c in scases); FN = len(scases) - TP
        FP = sum(fpc[m][c] for c in bcases);   TN = len(bcases) - FP
        P, N = TP + FN, TN + FP
        prec = TP / (TP + FP) if (TP + FP) else float("nan")
        rec, spec = TP / P, TN / N
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else float("nan")
        npv = TN / (TN + FN) if (TN + FN) else float("nan")
        den = math.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
        mcc = ((TP * TN) - (FP * FN)) / den if den else float("nan")
        per_model[NICE[m]] = {
            "family": FAM[m], "TP": TP, "FP": FP, "TN": TN, "FN": FN,
            "precision": prec, "precision_ci": list(wilson(TP, TP + FP)),
            "recall": rec, "recall_ci": list(wilson(TP, P)),
            "specificity": spec, "specificity_ci": list(wilson(TN, N)),
            "f1": f1, "balanced_accuracy": (rec + spec) / 2,
            "mcc": mcc, "accuracy": (TP + TN) / (P + N), "npv": npv,
            "fpr": FP / N, "miss_rate": FN / P, "n_pos": P, "n_neg": N,
        }

    # ---------- Cochran Q + McNemar on FP (unchanged; canonical benign flags) ----------
    mat = [[fpc[m][c] for m in models] for c in bcases]
    Q, df, pq = cochran_q(mat)
    pairs = {}
    mp = list(combinations(models, 2))
    for a, b in mp:
        bb = sum(1 for c in bcases if fpc[a][c] == 1 and fpc[b][c] == 0)
        cc = sum(1 for c in bcases if fpc[a][c] == 0 and fpc[b][c] == 1)
        p = mcnemar_exact(bb, cc)
        pairs[f"{NICE[a]} vs {NICE[b]}"] = {"b": bb, "c": cc, "p_exact": p,
                                            "p_bonferroni": min(1.0, p * len(mp))}

    # ---------- per-typology miss (ties->flag) ----------
    typ = defaultdict(lambda: [0, 0])
    for m in models:
        for c in scases:
            t = casetyp.get(c)
            if t:
                typ[t][1] += 1
                typ[t][0] += (1 - catch[m][c])
    typ_stats = {t: {"miss": k / n, "ci": list(wilson(k, n)), "k": k, "n": n}
                 for t, (k, n) in typ.items()}

    # ---------- per-typology x model miss matrix (for heatmap) ----------
    typs = sorted(typ_stats, key=lambda t: -typ_stats[t]["miss"])
    tm = {t: {} for t in typs}
    for t in typs:
        for m in models:
            cs = [c for c in scases if casetyp.get(c) == t]
            tm[t][NICE[m]] = (sum(1 - catch[m][c] for c in cs) / len(cs)) if cs else float("nan")

    # ---------- prompt sensitivity: per-model FP per variant (modal over 2 seeds) ----------
    variants = sorted({r["prompt_variant"] for r in rows})
    psens = {}
    for m in models:
        psens[NICE[m]] = {}
        for var in variants:
            pv = per_case(rows, "benign", variant_filter=var).get(m, {})
            k = sum(pv.values()); n = len(pv)
            psens[NICE[m]][var] = {"fp": (k / n if n else None), "k": k, "n": n}

    # ============================ WRITE DATA ============================
    (OUT / "classification_metrics.json").write_text(json.dumps(
        {"method": "modal vote over 4 replicates, ties->flag (preregistered D4); "
                   "Wilson 95% CIs; N=300 benign + 300 suspicious; frozen capture, $0, no API calls",
         "per_model": per_model}, indent=2))
    # CSV + MD table
    cols = ["Model", "Family", "Precision", "Recall", "Specificity", "F1",
            "BalancedAcc", "MCC", "Accuracy", "NPV", "FPR", "MissRate"]
    with (OUT / "classification_metrics.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for m in models:
            d = per_model[NICE[m]]
            w.writerow([NICE[m], d["family"], f"{d['precision']*100:.1f}", f"{d['recall']*100:.1f}",
                        f"{d['specificity']*100:.1f}", f"{d['f1']*100:.1f}", f"{d['balanced_accuracy']*100:.1f}",
                        f"{d['mcc']:.3f}", f"{d['accuracy']*100:.1f}", f"{d['npv']*100:.1f}",
                        f"{d['fpr']*100:.1f}", f"{d['miss_rate']*100:.1f}"])
    md = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for m in models:
        d = per_model[NICE[m]]
        md.append(f"| {NICE[m]} | {d['family']} | {d['precision']*100:.1f} "
                  f"[{d['precision_ci'][0]*100:.1f}–{d['precision_ci'][1]*100:.1f}] | "
                  f"{d['recall']*100:.1f} [{d['recall_ci'][0]*100:.1f}–{d['recall_ci'][1]*100:.1f}] | "
                  f"{d['specificity']*100:.1f} [{d['specificity_ci'][0]*100:.1f}–{d['specificity_ci'][1]*100:.1f}] | "
                  f"{d['f1']*100:.1f} | {d['balanced_accuracy']*100:.1f} | {d['mcc']:.3f} | "
                  f"{d['accuracy']*100:.1f} | {d['npv']*100:.1f} | {d['fpr']*100:.1f} | {d['miss_rate']*100:.1f} |")
    (OUT / "classification_metrics.md").write_text("\n".join(md))

    (OUT / "stats_tests_corrected.json").write_text(json.dumps(
        {"tie_rule": "ties->flag (preregistered D4) applied to BOTH tables and figures",
         "cochran_q": {"Q": Q, "df": df, "p": pq, "n_cases": len(bcases), "k_models": len(models)},
         "pairwise_mcnemar": pairs,
         "per_model_fp_miss": {NICE[m]: {"fp": per_model[NICE[m]]["fpr"],
                                         "miss": per_model[NICE[m]]["miss_rate"]} for m in models},
         "per_typology_miss": typ_stats}, indent=2, sort_keys=True, default=float))

    with (OUT / "prompt_sensitivity.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["Model"] + variants + ["delta_pp"])
        for m in models:
            a = psens[NICE[m]][variants[0]]["fp"]; b = psens[NICE[m]][variants[1]]["fp"]
            w.writerow([NICE[m], f"{a*100:.1f}", f"{b*100:.1f}", f"{(b-a)*100:+.1f}"])
    (OUT / "prompt_sensitivity.json").write_text(json.dumps(psens, indent=2))

    # ============================ FIGURES ============================
    def save(fig, name):
        fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
        fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    def despine(ax):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)

    # Fig 1 — per-model FP rate (unchanged rule; regenerated)
    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    fps = [per_model[NICE[m]]["fpr"] * 100 for m in models]
    err = [[(per_model[NICE[m]]["fpr"] - wilson(per_model[NICE[m]]["FP"], per_model[NICE[m]]["n_neg"])[0]) * 100 for m in models],
           [(wilson(per_model[NICE[m]]["FP"], per_model[NICE[m]]["n_neg"])[1] - per_model[NICE[m]]["fpr"]) * 100 for m in models]]
    ax.bar(range(len(models)), fps, yerr=err, capsize=4, color=BLUE, edgecolor="black", linewidth=0.6)
    ax.set_xticks(range(len(models))); ax.set_xticklabels([NICE[m] for m in models], rotation=20, ha="right")
    ax.set_ylabel("False-positive rate (%)"); ax.set_ylim(0, 100); despine(ax)
    save(fig, "fig1_fp_by_model")

    # Fig 2 — operating points (sensitivity vs FP) CORRECTED (ties->flag sensitivity)
    fig, ax = plt.subplots(figsize=(4.8, 4.3))
    for m in models:
        x = per_model[NICE[m]]["fpr"] * 100; y = per_model[NICE[m]]["recall"] * 100
        ax.scatter(x, y, s=60, color=BLUE, edgecolor="black", zorder=3)
        ax.annotate(NICE[m], (x, y), textcoords="offset points", xytext=(6, -3), fontsize=8)
    for name, (fp, miss), col in [("Rules", (0.12, 0.113), RED), ("Supervised", (0.0, 0.0), GREEN)]:
        ax.scatter(fp * 100, (1 - miss) * 100, s=60, marker="^", color=col, edgecolor="black", zorder=3)
        ax.annotate(name, (fp * 100, (1 - miss) * 100), textcoords="offset points", xytext=(6, -3), fontsize=8)
    ax.set_xlabel("False-positive rate (%)"); ax.set_ylabel("Sensitivity (% suspicious caught)")
    ax.set_xlim(-3, 100); ax.set_ylim(80, 101); despine(ax)
    save(fig, "fig2_operating_points")

    # Fig 3 — projected daily alert volume @ 0.1% prevalence (log)
    N, p = 1_000_000, 0.001
    def alerts(fp, miss): return fp * N * (1 - p) + (1 - miss) * N * p
    scr = [(NICE[m], per_model[NICE[m]]["fpr"], per_model[NICE[m]]["miss_rate"]) for m in models]
    scr += [("Rules", 0.12, 0.113), ("Supervised", 0.0, 0.0)]
    scr.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    vals = [alerts(fp, mi) for _n, fp, mi in scr]
    cols = [GREEN if n == "Supervised" else (RED if n == "Rules" else BLUE) for n, _f, _m in scr]
    ax.bar(range(len(scr)), vals, color=cols, edgecolor="black", linewidth=0.6)
    ax.set_yscale("log")
    ax.set_xticks(range(len(scr))); ax.set_xticklabels([n for n, _f, _m in scr], rotation=25, ha="right")
    ax.set_ylabel("Projected daily alerts (log scale)"); despine(ax)
    save(fig, "fig3_alert_volume")

    # Fig 4 — per-typology miss CORRECTED (ties->flag)
    tp = sorted(typ_stats, key=lambda t: -typ_stats[t]["miss"])
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ys = [typ_stats[t]["miss"] * 100 for t in tp]
    err = [[(typ_stats[t]["miss"] - typ_stats[t]["ci"][0]) * 100 for t in tp],
           [(typ_stats[t]["ci"][1] - typ_stats[t]["miss"]) * 100 for t in tp]]
    ax.bar(range(len(tp)), ys, yerr=err, capsize=3, color=PURPLE, edgecolor="black", linewidth=0.6)
    ax.set_xticks(range(len(tp))); ax.set_xticklabels([t.replace("_", " ") for t in tp], rotation=30, ha="right")
    ax.set_ylabel("Miss rate (%, pooled over models)"); despine(ax)
    save(fig, "fig4_typology_miss")

    # Fig 5 — typology x model miss heatmap CORRECTED
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    cmap = LinearSegmentedColormap.from_list("wm", ["#ffffff", PURPLE])
    M = [[tm[t][NICE[m]] * 100 for m in models] for t in typs]
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(models))); ax.set_xticklabels([NICE[m] for m in models], rotation=20, ha="right")
    ax.set_yticks(range(len(typs))); ax.set_yticklabels([t.replace("_", " ") for t in typs])
    for i in range(len(typs)):
        for j in range(len(models)):
            v = M[i][j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                    color="white" if v > 55 else "black", fontsize=7)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.set_label("Miss rate (%)")
    save(fig, "fig5_typology_model_heatmap")

    # Fig 6 — NEW: per-model classification metrics (grouped bars)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    mets = [("Precision", "precision", BLUE), ("Recall", "recall", GREEN),
            ("Specificity", "specificity", RED), ("F1", "f1", PURPLE)]
    w = 0.2
    for i, (lab, key, col) in enumerate(mets):
        ax.bar([x + (i - 1.5) * w for x in range(len(models))],
               [per_model[NICE[m]][key] * 100 for m in models], w, label=lab, color=col, edgecolor="black", linewidth=0.4)
    ax.set_xticks(range(len(models))); ax.set_xticklabels([NICE[m] for m in models], rotation=20, ha="right")
    ax.set_ylabel("Score (%)"); ax.set_ylim(0, 105); ax.legend(ncol=4, fontsize=8, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.42))
    despine(ax)
    save(fig, "fig6_classification_metrics")

    # Fig 7 — NEW: prompt sensitivity (per-model FP under each variant)
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    a = [psens[NICE[m]][variants[0]]["fp"] * 100 for m in models]
    b = [psens[NICE[m]][variants[1]]["fp"] * 100 for m in models]
    ax.bar([x - 0.2 for x in range(len(models))], a, 0.4, label=variants[0], color=BLUE, edgecolor="black", linewidth=0.4)
    ax.bar([x + 0.2 for x in range(len(models))], b, 0.4, label=variants[1], color=RED, edgecolor="black", linewidth=0.4)
    ax.set_xticks(range(len(models))); ax.set_xticklabels([NICE[m] for m in models], rotation=20, ha="right")
    ax.set_ylabel("False-positive rate (%)"); ax.set_ylim(0, 100)
    ax.legend(title="Prompt variant", fontsize=8, frameon=False); despine(ax)
    save(fig, "fig7_prompt_sensitivity")

    # ---- console summary ----
    print(f"[ext] models={models}")
    print(f"[ext] Cochran Q={Q:.1f} df={df} p={pq:.2e} (benign n={len(bcases)})  [FP side, unchanged]")
    print("[ext] per-model metrics (ties->flag):")
    for m in models:
        d = per_model[NICE[m]]
        print(f"    {NICE[m]:18} P={d['precision']*100:5.1f} R={d['recall']*100:5.1f} "
              f"Spec={d['specificity']*100:5.1f} F1={d['f1']*100:5.1f} MCC={d['mcc']:.3f} "
              f"FPR={d['fpr']*100:5.1f} Miss={d['miss_rate']*100:4.1f}")
    print("[ext] prompt sensitivity (FP per variant):")
    for m in models:
        a0 = psens[NICE[m]][variants[0]]["fp"] * 100; b0 = psens[NICE[m]][variants[1]]["fp"] * 100
        print(f"    {NICE[m]:18} {variants[0]}={a0:5.1f}  {variants[1]}={b0:5.1f}  d={b0-a0:+5.1f}")
    print(f"[ext] wrote 7 figures (pdf+png) + 4 data files to {OUT}")


if __name__ == "__main__":
    main()
