"""Regenerate every manuscript figure from the frozen capture corpus.

No figure generator was shipped with the original submission: the five PDFs were
orphaned artifacts with no code behind them, so they could not be re-derived and
silently went stale when the aggregation rule was corrected. This module closes that
gap. All figures use the canonical preregistered D4 rule in `aggregate.py`.

  fig1  false-positive rate per model, Wilson 95% intervals
  fig2  operating points, sensitivity against false-positive rate, with baselines
  fig3  projected daily alert volume at 0.1% prevalence
  fig4  miss rate by laundering typology
  fig5  typology x model miss heatmap
  fig6  prevalence sweep of alert volume and precision   (Reviewer 2, comment 8)

Deterministic and offline. Writes PDF (for the manuscript) and PNG (for the DOCX).
"""
from __future__ import annotations
import csv, glob, json, math, os, sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggregate as AGG  # noqa: E402

NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
        "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
        "openai_4o": "GPT-4o"}
ORDER = ["gemini_flash", "openai_4o", "openai_41_mini", "gemini_flash_lite", "openai_4o_mini"]
FAMCOL = {"gemini_flash": "#1a7f5a", "gemini_flash_lite": "#6fbf9a",
          "openai_4o": "#1f4e9c", "openai_41_mini": "#5a8ed0", "openai_4o_mini": "#a8c4e8"}
PREVALENCES = [0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01]
DAILY_N = 1_000_000

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 200, "savefig.bbox": "tight", "pdf.fonttype": 42})


def _capture_dir() -> Path:
    c = os.environ.get("POD_DATA_DIR")
    if c and (Path(c) / "capture").is_dir():
        return Path(c) / "capture"
    here = Path(__file__).resolve()
    for cand in (here.parents[1] / "data" / "capture", here.parents[1] / "data" / "raw"):
        if cand.is_dir():
            return cand
    raise FileNotFoundError("no capture directory")


def _outdirs():
    r = os.environ.get("POD_RESULTS_DIR")
    res = Path(r) if r else Path(__file__).resolve().parents[1] / "results"
    figs = res / "figures"; figs.mkdir(parents=True, exist_ok=True)
    tex = Path(__file__).resolve().parents[1] / "paper"
    return figs, (tex if tex.is_dir() else None)


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _load():
    votes = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    typ = {}
    for f in sorted(glob.glob(str(_capture_dir() / "runs_full_*.csv"))):
        if os.path.getsize(f) == 0 or "xai_grok" in f:
            continue
        for r in csv.DictReader(open(f)):
            if r.get("mode") != "REAL" or r["decision"] == "ERROR":
                continue
            votes[r["model_key"]][r["label"]][r["case_id"]].append(1 if r["decision"] == "flag" else 0)
            if r["label"] == "suspicious":
                typ[r["case_id"]] = r["typology"]
    return votes, typ


# matplotlib stamps /CreationDate into PDF output, which would make every re-run
# differ. Setting it to None makes the figures byte-reproducible so they can be hashed
# alongside the numeric outputs.
_PDF_META = {"CreationDate": None}


def _save(fig, figs, tex, name):
    fig.savefig(figs / f"{name}.pdf", metadata=_PDF_META)
    fig.savefig(figs / f"{name}.png", metadata={"Software": None})
    if tex:
        fig.savefig(tex / f"{name}.pdf", metadata=_PDF_META)
        fig.savefig(tex / f"{name}.png", metadata={"Software": None})
    plt.close(fig)


def run():
    votes, typ = _load()
    figs, tex = _outdirs()
    models = [m for m in ORDER if m in votes]
    bc = sorted(set.intersection(*[set(votes[m]["benign"]) for m in models]))
    sc = sorted(set.intersection(*[set(votes[m]["suspicious"]) for m in models]))
    A = AGG.modal_flag_from_votes

    fp = {m: sum(A(votes[m]["benign"][c]) for c in bc) for m in models}
    tp = {m: sum(A(votes[m]["suspicious"][c]) for c in sc) for m in models}
    fpr = {m: fp[m] / len(bc) for m in models}
    rec = {m: tp[m] / len(sc) for m in models}

    # ── fig1: FP rate per model with Wilson intervals ───────────────────────
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    x = range(len(models))
    lo = [100 * (fpr[m] - _wilson(fp[m], len(bc))[0]) for m in models]
    hi = [100 * (_wilson(fp[m], len(bc))[1] - fpr[m]) for m in models]
    ax.bar(x, [100 * fpr[m] for m in models], color=[FAMCOL[m] for m in models],
           yerr=[lo, hi], capsize=3, error_kw={"lw": 0.9})
    for i, m in enumerate(models):
        # clear the upper Wilson cap, not the mean, or the label sits on the whisker
        ax.text(i, 100 * fpr[m] + hi[i] + 2.2, f"{100*fpr[m]:.1f}%",
                ha="center", fontsize=8.5)
    ax.set_xticks(list(x)); ax.set_xticklabels([NICE[m] for m in models], rotation=18, ha="right")
    ax.set_ylabel("False-positive rate (%)")
    ax.set_title("False positives on 300 identical legitimate transactions", fontsize=9.5)
    ax.set_ylim(0, 100); ax.grid(axis="y", lw=0.4, alpha=0.4)
    _save(fig, figs, tex, "fig1_fp_by_model")

    # ── fig2: operating points ──────────────────────────────────────────────
    base = {}
    bp = Path(figs.parent / "baselines.json")
    if bp.exists():
        b = json.loads(bp.read_text())
        if "rules" in b:
            base["Rules heuristic"] = (100 * b["rules"]["fp"], 100 * (1 - b["rules"]["miss"]))
        gb = b.get("supervised", {}).get("grad_boost")
        if gb:
            base["Supervised (ceiling)"] = (100 * gb["fp"], 100 * (1 - gb["miss"]))
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    for m in models:
        ax.scatter(100 * fpr[m], 100 * rec[m], s=70, color=FAMCOL[m], zorder=3,
                   edgecolor="white", lw=0.8)
        ax.annotate(NICE[m], (100 * fpr[m], 100 * rec[m]), textcoords="offset points",
                    xytext=(7, -3), fontsize=8)
    for nm, (bx, by) in base.items():
        ax.scatter(bx, by, marker="^", s=70, color="#777777", zorder=3)
        ax.annotate(nm, (bx, by), textcoords="offset points", xytext=(7, -3), fontsize=8)
    ax.set_xlabel("False-positive rate (%)"); ax.set_ylabel("Sensitivity (%)")
    ax.set_title("Each model occupies a different operating point", fontsize=9.5)
    ax.set_xlim(-4, 100); ax.set_ylim(80, 101.5); ax.grid(lw=0.4, alpha=0.4)
    _save(fig, figs, tex, "fig2_operating_points")

    # ── fig3: projected daily alert volume ──────────────────────────────────
    pi = 0.001
    vol = {m: DAILY_N * (pi * rec[m] + (1 - pi) * fpr[m]) for m in models}
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    ax.bar(x, [vol[m] for m in models], color=[FAMCOL[m] for m in models])
    for i, m in enumerate(models):
        ax.text(i, vol[m] * 1.35, f"{vol[m]:,.0f}", ha="center", fontsize=8.5)
    ax.set_yscale("log"); ax.set_ylim(1e3, 3e6)
    ax.set_xticks(list(x)); ax.set_xticklabels([NICE[m] for m in models], rotation=18, ha="right")
    ax.set_ylabel("Projected alerts per day (log scale)")
    ax.set_title("Projected daily alerts, 1,000,000 transactions at 0.1% prevalence", fontsize=9.5)
    ax.grid(axis="y", lw=0.4, alpha=0.4)
    _save(fig, figs, tex, "fig3_alert_volume")

    # ── fig4 / fig5: typology misses ────────────────────────────────────────
    typs = sorted({typ[c] for c in sc if typ.get(c)})
    cell = {(m, t): [] for m in models for t in typs}
    for m in models:
        for c in sc:
            t = typ.get(c)
            if t:
                cell[(m, t)].append(1 - A(votes[m]["suspicious"][c]))
    tmiss = {t: sum(sum(cell[(m, t)]) for m in models) / sum(len(cell[(m, t)]) for m in models)
             for t in typs}
    order_t = sorted(typs, key=lambda t: -tmiss[t])
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.bar(range(len(order_t)), [100 * tmiss[t] for t in order_t], color="#b4472e")
    ax.set_xticks(range(len(order_t)))
    ax.set_xticklabels([t.replace("_", " ") for t in order_t], rotation=28, ha="right", fontsize=8)
    ax.set_ylabel("Miss rate (%)")
    ax.set_title("Miss rate by laundering typology, pooled across models", fontsize=9.5)
    ax.grid(axis="y", lw=0.4, alpha=0.4)
    _save(fig, figs, tex, "fig4_typology_miss")

    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    M = [[100 * (sum(cell[(m, t)]) / len(cell[(m, t)])) for m in models] for t in order_t]
    im = ax.imshow(M, cmap="Reds", aspect="auto", vmin=0, vmax=max(max(r) for r in M) or 1)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([NICE[m] for m in models], rotation=28, ha="right", fontsize=8)
    ax.set_yticks(range(len(order_t)))
    ax.set_yticklabels([t.replace("_", " ") for t in order_t], fontsize=8)
    for i in range(len(order_t)):
        for j in range(len(models)):
            ax.text(j, i, f"{M[i][j]:.0f}", ha="center", va="center", fontsize=7.5,
                    color="white" if M[i][j] > 0.6 * max(max(r) for r in M) else "#222222")
    fig.colorbar(im, ax=ax, label="Miss rate (%)", fraction=0.045)
    ax.set_title("Miss rate by typology and model", fontsize=9.5)
    _save(fig, figs, tex, "fig5_typology_model_heatmap")

    # ── fig6: prevalence sweep (Reviewer 2, comment 8) ──────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.6))
    handles = []
    for m in models:
        v = [DAILY_N * (p * rec[m] + (1 - p) * fpr[m]) for p in PREVALENCES]
        pr = [100 * p * rec[m] / (p * rec[m] + (1 - p) * fpr[m]) for p in PREVALENCES]
        ln, = axes[0].plot([100 * p for p in PREVALENCES], v, marker="o", ms=3.2,
                           color=FAMCOL[m], label=NICE[m], lw=1.4)
        handles.append(ln)
        axes[1].plot([100 * p for p in PREVALENCES], pr, marker="o", ms=3.2,
                     color=FAMCOL[m], lw=1.4)
    for a, yl, ti in ((axes[0], "Projected alerts per day", "Alert volume"),
                      (axes[1], "Precision (%)", "Precision")):
        a.set_xscale("log"); a.set_xlabel("Suspicious-activity prevalence (%)")
        a.set_ylabel(yl); a.set_title(ti, fontsize=9); a.grid(lw=0.4, alpha=0.4)
    axes[0].set_yscale("log")
    axes[0].set_ylim(1e4, 2e6)                      # keep the lowest curve clear of the axis
    ratios = [max(DAILY_N * (p * rec[m] + (1 - p) * fpr[m]) for m in models)
              / min(DAILY_N * (p * rec[m] + (1 - p) * fpr[m]) for m in models) for p in PREVALENCES]
    # legend below the panels: inside the axes it sat on top of the lowest curve
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=7.5,
               frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Model ordering is invariant across prevalence; ratio "
                 f"{min(ratios):.0f}\u2013{max(ratios):.0f}-fold", fontsize=9.5, y=1.02)
    fig.tight_layout()
    _save(fig, figs, tex, "fig6_prevalence_sweep")

    return {"figures": 6, "fpr": fpr, "recall": rec,
            "alert_ratio_at_0.1pct": max(vol.values()) / min(vol.values()),
            "sweep_ratio_range": [min(ratios), max(ratios)]}


if __name__ == "__main__":
    r = run()
    print(f"[figures] wrote {r['figures']} figures; alert ratio at 0.1% = "
          f"{r['alert_ratio_at_0.1pct']:.1f}-fold; across prevalence "
          f"{r['sweep_ratio_range'][0]:.1f}-{r['sweep_ratio_range'][1]:.1f}-fold")
