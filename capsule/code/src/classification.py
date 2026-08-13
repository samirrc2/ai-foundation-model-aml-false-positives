"""Standard classification metrics + paired inferential tests for the capsule.

Deterministic, offline, $0. Reads the FROZEN capture CSVs and emits, from the
SAME modal-vote decisions used for Table 1 (ties -> flag, preregistered D4):

  classification_metrics.json   per-model precision/recall/specificity/F1/
                                balanced-accuracy/MCC/accuracy/NPV + Wilson 95% CIs
  stats_tests.json              Cochran's Q (overall FP difference) + pairwise
                                McNemar exact (Bonferroni) + per-model FP/miss +
                                per-typology miss  — ALL on the ties->flag rule so
                                tables and figures are mutually consistent
  prompt_sensitivity.json/.csv  per-model FP under each prompt variant

This module supersedes the earlier figures_stats.py miss computation, which broke
ties toward *miss* and therefore disagreed with Table 1; here every miss-side number
uses the preregistered ties->flag rule.
"""
from __future__ import annotations
import csv, glob, json, math, os
from collections import defaultdict
from itertools import combinations
from pathlib import Path

try:
    from scipy import stats as _sp
    _HAVE_SCIPY = True
except Exception:                                   # pragma: no cover
    _HAVE_SCIPY = False

NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
        "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
        "openai_4o": "GPT-4o"}
FAM = {"gemini_flash": "Google", "gemini_flash_lite": "Google", "openai_4o": "OpenAI",
       "openai_41_mini": "OpenAI", "openai_4o_mini": "OpenAI"}
ORDER = ["gemini_flash", "openai_4o", "openai_41_mini", "gemini_flash_lite", "openai_4o_mini"]


def _capture_dir() -> Path:
    for c in (os.environ.get("POD_DATA_DIR"), None):
        if c and (Path(c) / "capture").is_dir():
            return Path(c) / "capture"
    here = Path(__file__).resolve()
    for cand in (here.parents[2] / "data" / "capture",       # codeocean/data/capture
                 here.parents[2] / "data" / "raw"):           # main tree data/raw
        if cand.is_dir():
            return cand
    raise FileNotFoundError("no capture directory (data/capture or data/raw)")


def _results_dir() -> Path:
    r = os.environ.get("POD_RESULTS_DIR")
    if r:
        Path(r).mkdir(parents=True, exist_ok=True); return Path(r)
    here = Path(__file__).resolve()
    out = here.parents[2] / "results"; out.mkdir(parents=True, exist_ok=True); return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _load(cap: Path):
    rows = []
    for f in glob.glob(str(cap / "runs_full_*.csv")):
        if os.path.getsize(f) == 0 or "xai_grok" in f:
            continue
        for r in csv.DictReader(open(f)):
            if r.get("mode") == "REAL":
                rows.append(r)
    return rows


def modal_flag(v):                       # benign: FP iff strict majority flagged (tie -> no FP)
    return 1 if sum(v) > len(v) / 2 else 0


def modal_caught(v):                     # suspicious: caught iff flags >= half (tie -> caught / not miss)
    return 1 if 2 * sum(v) >= len(v) else 0


def _per_case(rows, label, variant=None):
    rule = modal_caught if label == "suspicious" else modal_flag
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["label"] != label or r["decision"] == "ERROR":
            continue
        if variant is not None and r["prompt_variant"] != variant:
            continue
        acc[r["model_key"]][r["case_id"]].append(1 if r["decision"] == "flag" else 0)
    return {m: {c: rule(v) for c, v in d.items()} for m, d in acc.items()}


def cochran_q(mat):
    k = len(mat[0]); Cj = [sum(row[j] for row in mat) for j in range(k)]
    Ri = [sum(row) for row in mat]; Cbar = sum(Cj) / k
    num = (k - 1) * sum((c - Cbar) ** 2 for c in Cj)
    den = k * sum(Ri) - sum(r * r for r in Ri)
    Q = num / den if den else 0.0
    p = (1 - _sp.chi2.cdf(Q, k - 1)) if _HAVE_SCIPY else None
    return Q, k - 1, p


def mcnemar_exact(b, c):
    n = b + c
    if n == 0 or not _HAVE_SCIPY:
        return (1.0 if n == 0 else None)
    k = min(b, c)
    return min(1.0, 2 * sum(_sp.binom.pmf(i, n, 0.5) for i in range(k + 1)))


def run():
    cap = _capture_dir(); out = _results_dir()
    rows = _load(cap)
    fpc = _per_case(rows, "benign"); catch = _per_case(rows, "suspicious")
    models = [m for m in ORDER if m in fpc]
    bcases = sorted(set.intersection(*[set(fpc[m]) for m in models]))
    scases = sorted(set.intersection(*[set(catch[m]) for m in models]))
    casetyp = {r["case_id"]: r["typology"] for r in rows if r["label"] == "suspicious"}

    per_model = {}
    for m in models:
        TP = sum(catch[m][c] for c in scases); FN = len(scases) - TP
        FP = sum(fpc[m][c] for c in bcases);   TN = len(bcases) - FP
        P, N = TP + FN, TN + FP
        prec = TP / (TP + FP) if (TP + FP) else None
        rec, spec = TP / P, TN / N
        f1 = 2 * prec * rec / (prec + rec) if prec else None
        den = math.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
        mcc = ((TP * TN) - (FP * FN)) / den if den else None
        per_model[NICE[m]] = {
            "family": FAM[m], "TP": TP, "FP": FP, "TN": TN, "FN": FN,
            "precision": prec, "precision_ci": list(wilson(TP, TP + FP)),
            "recall": rec, "recall_ci": list(wilson(TP, P)),
            "specificity": spec, "specificity_ci": list(wilson(TN, N)),
            "f1": f1, "balanced_accuracy": (rec + spec) / 2,
            "mcc": mcc, "accuracy": (TP + TN) / (P + N),
            "npv": TN / (TN + FN) if (TN + FN) else None,
            "fpr": FP / N, "miss_rate": FN / P, "n_pos": P, "n_neg": N}

    mat = [[fpc[m][c] for m in models] for c in bcases]
    Q, df, pq = cochran_q(mat)
    pairs = {}
    mp = list(combinations(models, 2))
    for a, b in mp:
        bb = sum(1 for c in bcases if fpc[a][c] == 1 and fpc[b][c] == 0)
        cc = sum(1 for c in bcases if fpc[a][c] == 0 and fpc[b][c] == 1)
        p = mcnemar_exact(bb, cc)
        pairs[f"{NICE[a]} vs {NICE[b]}"] = {
            "b": bb, "c": cc, "p_exact": p,
            "p_bonferroni": (min(1.0, p * len(mp)) if p is not None else None)}

    typ = defaultdict(lambda: [0, 0])
    for m in models:
        for c in scases:
            t = casetyp.get(c)
            if t:
                typ[t][1] += 1; typ[t][0] += (1 - catch[m][c])
    typ_stats = {t: {"miss": k / n, "ci": list(wilson(k, n)), "k": k, "n": n}
                 for t, (k, n) in typ.items()}

    variants = sorted({r["prompt_variant"] for r in rows})
    psens = {}
    for m in models:
        psens[NICE[m]] = {}
        for var in variants:
            pv = _per_case(rows, "benign", variant=var).get(m, {})
            k = sum(pv.values()); n = len(pv)
            psens[NICE[m]][var] = {"fp": (k / n if n else None), "k": k, "n": n}

    (out / "classification_metrics.json").write_text(json.dumps(
        {"method": "modal vote, ties->flag (D4); Wilson 95% CIs; N=300 benign + 300 suspicious",
         "per_model": per_model}, indent=2, sort_keys=True))
    with (out / "classification_metrics.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model", "Family", "Precision", "Recall", "Specificity", "F1",
                    "BalancedAcc", "MCC", "Accuracy", "NPV", "FPR", "MissRate"])
        for m in models:
            d = per_model[NICE[m]]
            w.writerow([NICE[m], d["family"]] + [f"{d[k]*100:.1f}" for k in
                       ("precision", "recall", "specificity", "f1", "balanced_accuracy")] +
                       [f"{d['mcc']:.3f}"] + [f"{d[k]*100:.1f}" for k in ("accuracy", "npv", "fpr", "miss_rate")])
    (out / "stats_tests.json").write_text(json.dumps(
        {"tie_rule": "ties->flag (D4), applied to tables AND figures",
         "cochran_q": {"Q": Q, "df": df, "p": pq, "n_cases": len(bcases), "k_models": len(models)},
         "pairwise_mcnemar": pairs,
         "per_model_fp_miss": {NICE[m]: {"fp": per_model[NICE[m]]["fpr"],
                                         "miss": per_model[NICE[m]]["miss_rate"]} for m in models},
         "per_typology_miss": typ_stats}, indent=2, sort_keys=True, default=float))
    (out / "prompt_sensitivity.json").write_text(json.dumps(psens, indent=2, sort_keys=True))
    with (out / "prompt_sensitivity.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["Model"] + variants + ["delta_pp"])
        for m in models:
            a = psens[NICE[m]][variants[0]]["fp"]; b = psens[NICE[m]][variants[1]]["fp"]
            w.writerow([NICE[m], f"{a*100:.1f}", f"{b*100:.1f}", f"{(b-a)*100:+.1f}"])

    return {"classification_metrics.json": per_model, "cochran_Q": Q}


if __name__ == "__main__":
    r = run()
    print(f"[classification] Cochran Q={r['cochran_Q']:.1f}; wrote classification_metrics.*, "
          f"stats_tests.json, prompt_sensitivity.* to results/")
