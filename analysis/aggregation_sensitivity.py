"""Aggregation-rule sensitivity analysis (editor; Reviewer 2 comment 5; Reviewer 3).

The primary rule is preregistered decision D4 in `aggregate.py`: modal flag over
replicates, ties resolved toward flag, label-independent. This module reports what
happens under the alternatives, so the headline cannot be an artifact of the rule:

  * ties -> flag                      the preregistered D4 rule (PRIMARY)
  * ties -> no flag                   strict majority, label-independent
  * ties -> abstention                tied cases dropped from the denominator
  * unanimity required to flag        label-independent
  * label-dependent (as published)    the deviation corrected in this revision
  * each of the four single calls     prompt variant x seed, no aggregation at all

It also emits the per-model tie census, adjacent-tier paired comparisons with
cluster-robust intervals over the typology strata, a cluster-level permutation test of
the overall false-positive heterogeneity, and the prevalence sweep of alert volume.

Deterministic, offline, $0. Reads only the frozen capture CSVs.
"""
from __future__ import annotations
import csv, glob, json, math, os, random, sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggregate as AGG  # noqa: E402

try:
    from scipy import stats as _sp
    _HAVE_SCIPY = True
except Exception:                                   # pragma: no cover
    _HAVE_SCIPY = False

NICE = {"gemini_flash": "Gemini Flash", "gemini_flash_lite": "Gemini Flash-Lite",
        "openai_4o_mini": "GPT-4o-mini", "openai_41_mini": "GPT-4.1-mini",
        "openai_4o": "GPT-4o"}
ORDER = ["gemini_flash", "openai_4o", "openai_41_mini", "gemini_flash_lite", "openai_4o_mini"]
TIERS = [("OpenAI", "openai_4o", "openai_41_mini"), ("OpenAI", "openai_41_mini", "openai_4o_mini"),
         ("Google", "gemini_flash", "gemini_flash_lite")]
DRAWS, SEED = 2000, 4242
PREVALENCES = [0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01]
DAILY_N = 1_000_000


def _capture_dir() -> Path:
    c = os.environ.get("POD_DATA_DIR")
    if c and (Path(c) / "capture").is_dir():
        return Path(c) / "capture"
    here = Path(__file__).resolve()
    for cand in (here.parents[1] / "data" / "capture", here.parents[1] / "data" / "raw"):
        if cand.is_dir():
            return cand
    raise FileNotFoundError("no capture directory")


def _results_dir() -> Path:
    r = os.environ.get("POD_RESULTS_DIR")
    out = Path(r) if r else Path(__file__).resolve().parents[1] / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── tie policies: each maps a list of 0/1 flags -> 0/1 flag, or None to abstain ──
def _tie_to_flag(v, label):      return AGG.modal_flag_from_votes(v)
def _tie_to_noflag(v, label):    return 1 if sum(v) > len(v) / 2 else 0
def _unanimous(v, label):        return 1 if sum(v) == len(v) else 0
def _abstain(v, label):
    return None if 2 * sum(v) == len(v) else (1 if 2 * sum(v) > len(v) else 0)
def _as_published(v, label):
    """The deviation this revision corrects: tie direction chosen by the case label."""
    return (1 if sum(v) > len(v) / 2 else 0) if label == "benign" else (1 if 2 * sum(v) >= len(v) else 0)


POLICIES = [
    ("ties_to_flag_preregistered_D4", _tie_to_flag, True),
    ("ties_to_no_flag_strict_majority", _tie_to_noflag, False),
    ("ties_as_abstention", _abstain, False),
    ("unanimity_required", _unanimous, False),
    ("label_dependent_as_published", _as_published, False),
]


def _load():
    votes = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    bycfg = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    strat, n_rows, n_err = {}, 0, 0
    for f in sorted(glob.glob(str(_capture_dir() / "runs_full_*.csv"))):
        if os.path.getsize(f) == 0 or "xai_grok" in f:
            continue
        for r in csv.DictReader(open(f)):
            if r.get("mode") != "REAL":
                continue
            n_rows += 1
            if r["decision"] == "ERROR":
                n_err += 1
                continue
            v = 1 if r["decision"] == "flag" else 0
            votes[r["model_key"]][r["label"]][r["case_id"]].append(v)
            bycfg[(r["prompt_variant"], r["seed_index"])][r["model_key"]][r["label"] + "|" + r["case_id"]].append(v)
            if r["label"] == "benign":
                strat[r["case_id"]] = r["stratum"]
    return votes, bycfg, strat, n_rows, n_err


def _cochran_q(mat):
    k = len(mat[0])
    Cj = [sum(row[j] for row in mat) for j in range(k)]
    Ri = [sum(row) for row in mat]
    Cbar = sum(Cj) / k
    den = k * sum(Ri) - sum(r * r for r in Ri)
    # Cochran's Q = k(k-1) * sum_j (C_j - Cbar)^2 / (k*sum_i R_i - sum_i R_i^2).
    # The factor k was missing from the numerator, which understated every Q in the submitted
    # and first-revised analyses by exactly fivefold (k = 5 models). Verified against
    # statsmodels.stats.contingency_tables.cochrans_q, which agrees to 1e-9 after the fix.
    Q = (k * (k - 1) * sum((c - Cbar) ** 2 for c in Cj) / den) if den else 0.0
    p = float(_sp.chi2.sf(Q, k - 1)) if _HAVE_SCIPY else None
    return Q, k - 1, p


def _mcnemar(b, c):
    n = b + c
    if n == 0 or not _HAVE_SCIPY:
        return 1.0 if n == 0 else None
    return min(1.0, 2 * sum(_sp.binom.pmf(i, n, 0.5) for i in range(min(b, c) + 1)))


def _sig(x, n=4):
    if x is None or x == 0.0:
        return x
    return float(f"{x:.{n}g}") if abs(x) < 1e-4 else round(x, n)


def run():
    votes, bycfg, strat, n_rows, n_err = _load()
    out = _results_dir()
    models = [m for m in ORDER if m in votes]
    bc = sorted(set.intersection(*[set(votes[m]["benign"]) for m in models]))
    sc = sorted(set.intersection(*[set(votes[m]["suspicious"]) for m in models]))

    # ── tie census ───────────────────────────────────────────────────────────
    census = {}
    for m in models:
        tb = sum(1 for c in bc if 2 * sum(votes[m]["benign"][c]) == len(votes[m]["benign"][c]))
        ts = sum(1 for c in sc if 2 * sum(votes[m]["suspicious"][c]) == len(votes[m]["suspicious"][c]))
        kdist = defaultdict(int)
        for lab, cs in (("benign", bc), ("suspicious", sc)):
            for c in cs:
                kdist[len(votes[m][lab][c])] += 1
        census[NICE[m]] = {"benign_ties": tb, "suspicious_ties": ts,
                           "valid_calls_per_case": dict(sorted(kdist.items()))}

    # ── each policy ──────────────────────────────────────────────────────────
    policies = {}
    for name, rule, is_primary in POLICIES:
        per, rawfp = {}, {}
        for m in models:
            fp = fpn = 0
            for c in bc:
                d = rule(votes[m]["benign"][c], "benign")
                if d is None:
                    continue
                fpn += 1; fp += d
            ms = msn = 0
            for c in sc:
                d = rule(votes[m]["suspicious"][c], "suspicious")
                if d is None:
                    continue
                msn += 1; ms += (1 - d)
            per[NICE[m]] = {"fp_rate": _sig(fp / fpn), "n_benign": fpn,
                            "miss_rate": _sig(ms / msn), "n_suspicious": msn}
            rawfp[m] = fp / fpn
        rates = [rawfp[m] for m in models]
        entry = {"primary": is_primary, "per_model": per,
                 "fp_spread_pp": _sig(100 * (max(rates) - min(rates)))}
        # Cochran's Q needs complete blocks: every model must have a decision on the case.
        # Under ties-as-abstention some (model, case) cells are None, so Q is computed on the
        # cases where all five models decided, and n_cases records how many that leaves. The
        # row used to be blank, which read as "not applicable" rather than "computed on a
        # reduced set".
        mat = [[rule(votes[m]["benign"][c], "benign") for m in models] for c in bc]
        mat = [row for row in mat if all(v is not None for v in row)]
        Q, df, pq = _cochran_q(mat)
        entry["cochran_q"] = {"Q": _sig(Q), "df": df, "p": _sig(pq), "n_cases": len(mat),
                              "Q_as_published_understated": _sig(Q / len(models)),
                              "Q_as_published_note": "the value published at submission and in the first revision, which omitted the factor k from the numerator and is therefore Q/k; retained so the correction is auditable"}
        policies[name] = entry

    # ── single-call configurations (no aggregation) ──────────────────────────
    singles = {}
    for cfg in sorted(bycfg):
        per, raw = {}, {}
        for m in models:
            d = bycfg[cfg][m]
            bn = [v[0] for k, v in d.items() if k.startswith("benign|")]
            sp = [v[0] for k, v in d.items() if k.startswith("suspicious|")]
            # keep the UNROUNDED rates for the projection; rounding a rate of 0.003333
            # to 4 d.p. before projecting shifts the alert ratio by ~1 percent
            raw[m] = (sum(bn) / len(bn), sum(sp) / len(sp))
            per[NICE[m]] = {"fp_rate": _sig(raw[m][0]), "miss_rate": _sig(1 - raw[m][1])}
        rates = [raw[m][0] for m in models]
        vol = {NICE[m]: DAILY_N * (0.001 * raw[m][1] + 0.999 * raw[m][0]) for m in models}
        # Q on the single call itself: the same heterogeneity test applied to a deployable
        # configuration rather than to the four-call aggregate.
        bkeys = sorted(k for k in bycfg[cfg][models[0]] if k.startswith("benign|"))
        smat = [[bycfg[cfg][m][k][0] for m in models] for k in bkeys]
        smat = [row for row in smat if all(v is not None for v in row)]
        sQ, sdf, sp = _cochran_q(smat)
        singles[f"{cfg[0]}|seed{cfg[1]}"] = {
            "per_model": per, "fp_spread_pp": _sig(100 * (max(rates) - min(rates))),
            "cochran_q": {"Q": _sig(sQ), "df": sdf, "p": _sig(sp), "n_cases": len(smat),
                          "Q_as_published_understated": _sig(sQ / len(models)),
                          "Q_as_published_note": "the value published at submission and in the first revision, which omitted the factor k from the numerator and is therefore Q/k; retained so the correction is auditable"},
            "alert_volume_at_0.1pct": {k: round(v) for k, v in vol.items()},
            "alert_ratio_max_over_min": _sig(max(vol.values()) / min(vol.values()))}

    # ── adjacent-tier paired tests + cluster-robust step intervals ───────────
    by = defaultdict(list)
    for c in bc:
        by[strat[c]].append(c)
    keys = sorted(by)

    def cluster_ci(stat_fn):
        rng = random.Random(SEED); vals = []
        for _ in range(DRAWS):
            rs = []
            for _i in range(len(keys)):
                rs.extend(by[keys[rng.randrange(len(keys))]])
            vals.append(stat_fn(rs))
        vals.sort()
        return _sig(vals[int(0.025 * DRAWS)]), _sig(vals[int(0.975 * DRAWS) - 1])

    rule = _tie_to_flag
    tier = {}
    for fam, a, b in TIERS:
        bb = sum(1 for c in bc if rule(votes[a]["benign"][c], "benign") == 1 and rule(votes[b]["benign"][c], "benign") == 0)
        cc = sum(1 for c in bc if rule(votes[a]["benign"][c], "benign") == 0 and rule(votes[b]["benign"][c], "benign") == 1)
        p = _mcnemar(bb, cc)
        pt = 100 * (sum(rule(votes[b]["benign"][c], "benign") for c in bc)
                    - sum(rule(votes[a]["benign"][c], "benign") for c in bc)) / len(bc)
        lo, hi = cluster_ci(lambda cs, a=a, b=b: 100 * (sum(rule(votes[b]["benign"][c], "benign") for c in cs)
                                                        - sum(rule(votes[a]["benign"][c], "benign") for c in cs)) / len(cs))
        tier[f"{NICE[a]} -> {NICE[b]}"] = {
            "family": fam, "b": bb, "c": cc, "p_exact": _sig(p),
            "p_bonferroni3": _sig(min(1.0, p * 3)) if p is not None else None,
            "fp_difference_pp": _sig(pt), "cluster_ci95_pp": [lo, hi],
            "ci_excludes_zero": bool(lo > 0 or hi < 0)}

    # ── cluster-level permutation test of overall FP heterogeneity ───────────
    def q_on(cs):
        return _cochran_q([[rule(votes[m]["benign"][c], "benign") for m in models] for c in cs])[0]
    obs = q_on(bc)
    rng = random.Random(99); ge = 0
    order = list(range(len(models)))
    for _ in range(DRAWS):
        # One permutation of the model labels per stratum, applied to EVERY case in that
        # stratum. The previous version drew a fresh permutation for each case
        # (rng.shuffle(row) inside the case loop), which destroys the within-stratum
        # dependence the test exists to respect: permuting independently within each case
        # makes the cases exchangeable again and so does not account for clustering. The
        # bootstrap resampling of strata that wrapped this loop is also gone -- this is a
        # permutation test, and resampling clusters inside it conflated two procedures.
        mat = []
        for k in keys:
            pi = order[:]
            rng.shuffle(pi)
            for c in by[k]:
                row = [rule(votes[m]["benign"][c], "benign") for m in models]
                mat.append([row[i] for i in pi])
        if _cochran_q(mat)[0] >= obs:
            ge += 1
    perm = {"statistic": "Cochran Q", "observed": _sig(obs), "draws": DRAWS,
            "n_strata": len(keys), "n_at_or_above_observed": ge,
            "scheme": "one permutation of model labels per typology stratum, applied to all "
                      "cases in that stratum",
            "p": _sig((ge + 1) / (DRAWS + 1))}

    # ── abstention on the COMMON retained subset ─────────────────────────────────
    # Under ties-as-abstention each model keeps a different set of cases, so the headline
    # spread compares five rates estimated on five different subsets. This recomputes all
    # five on the cases every model retained, which is the like-for-like comparison, and is
    # reported alongside the model-specific figure rather than replacing it.
    _ab = lambda v: None if 2 * sum(v) == len(v) else (1 if 2 * sum(v) > len(v) else 0)
    common = [c for c in bc if all(_ab(votes[m]["benign"][c]) is not None for m in models)]
    cm = {NICE[m]: _sig(sum(_ab(votes[m]["benign"][c]) for c in common) / len(common))
          for m in models} if common else {}
    _cr = [cm[NICE[m]] for m in models] if common else [0]
    abstention_common = {
        "n_cases": len(common),
        "per_model_fp_rate": cm,
        "fp_spread_pp": _sig(100 * (max(_cr) - min(_cr))),
        "note": ("all five rates on the cases every model retained; the headline abstention row "
                 "uses each model's own retained cases, so its spread compares different subsets")}

    # ── sensitivity: restrict the vote to the four DESIGNED prompt-seed cells ─────
    # D4 defines the vote over valid replicate calls, so the primary analysis uses all of them,
    # including the 111 duplicated GPT-4o-mini terse/seed-0 calls. This reports what the rates
    # would be if each (model, case) voted over one call per designed cell instead, so the
    # manuscript quotes a derived number rather than a hand-computed one.
    four = {}
    for m in models:
        fp = 0
        for c in bc:
            seen, ded = set(), []
            for cfg in sorted(bycfg):
                k = "benign|" + c
                if k in bycfg[cfg][m] and cfg not in seen:
                    seen.add(cfg); ded.append(bycfg[cfg][m][k][0])
            fp += _tie_to_flag(ded, "benign")
        four[NICE[m]] = {"fp_rate": _sig(fp / len(bc)), "n_benign": len(bc)}
    _fr = [four[NICE[m]]["fp_rate"] for m in models]
    four_cell = {"per_model": four,
                 "fp_spread_pp": _sig(100 * (max(_fr) - min(_fr))),
                 "note": ("one call per designed prompt-seed cell; the primary analysis votes over "
                          "all valid calls, per D4")}

    # ── prevalence sweep under the primary rule ──────────────────────────────
    fpr = {m: sum(rule(votes[m]["benign"][c], "benign") for c in bc) / len(bc) for m in models}
    rec = {m: sum(rule(votes[m]["suspicious"][c], "suspicious") for c in sc) / len(sc) for m in models}
    sweep = []
    for pi in PREVALENCES:
        vol = {NICE[m]: DAILY_N * (pi * rec[m] + (1 - pi) * fpr[m]) for m in models}
        prec = {NICE[m]: 100 * pi * rec[m] / (pi * rec[m] + (1 - pi) * fpr[m]) for m in models}
        sweep.append({"prevalence": pi, "alerts": {k: round(v) for k, v in vol.items()},
                      "precision_pct": {k: _sig(v) for k, v in prec.items()},
                      "ratio_max_over_min": _sig(max(vol.values()) / min(vol.values()))}) 

    ratios = [s["ratio_max_over_min"] for s in sweep] + [v["alert_ratio_max_over_min"] for v in singles.values()]
    payload = {
        "abstention_common_subset": abstention_common,
        "four_designed_cells_sensitivity": four_cell,
        "primary_rule": "preregistered decision D4: modal flag over replicates, ties -> flag, label-independent",
        "deviation_corrected": ("the submitted analysis required a strict majority on legitimate cases, so a 2-2 tie "
                                "was not counted as a false positive; the tie direction therefore depended on the "
                                "ground-truth label. D4 specifies ties -> flag for both labels."),
        "calls": {"designed": 12000, "realized": n_rows, "errors": n_err,
                  "error_rate": _sig(n_err / n_rows)},
        "tie_census": census,
        "policies": policies,
        "single_call_configurations": singles,
        "fp_spread_range_pp": [_sig(min([policies[n]["fp_spread_pp"] for n, _, _ in POLICIES]
                                        + [v["fp_spread_pp"] for v in singles.values()])),
                               _sig(max([policies[n]["fp_spread_pp"] for n, _, _ in POLICIES]
                                        + [v["fp_spread_pp"] for v in singles.values()]))],
        "adjacent_tier": tier,
        "cluster_permutation": perm,
        "prevalence_sweep": sweep,
        "alert_ratio_range_deployable": [_sig(min(v["alert_ratio_max_over_min"] for v in singles.values())),
                                         _sig(max(v["alert_ratio_max_over_min"] for v in singles.values()))],
    }
    (out / "aggregation_sensitivity.json").write_text(json.dumps(payload, indent=2, sort_keys=True))

    # ── manuscript table: policies x models, both axes ──────────────────────
    with (out / "table5_aggregation_sensitivity.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Rule"] + [NICE[m] + " FP%" for m in models] + ["FP spread pp"]
                   + [NICE[m] + " miss%" for m in models])
        for name, _, _ in POLICIES:
            e = policies[name]
            w.writerow([name]
                       + [f"{e['per_model'][NICE[m]]['fp_rate']*100:.1f}" for m in models]
                       + [f"{e['fp_spread_pp']:.1f}"]
                       + [f"{e['per_model'][NICE[m]]['miss_rate']*100:.1f}" for m in models])
        for k, e in singles.items():
            w.writerow([f"single call: {k}"]
                       + [f"{e['per_model'][NICE[m]]['fp_rate']*100:.1f}" for m in models]
                       + [f"{e['fp_spread_pp']:.1f}"]
                       + [f"{e['per_model'][NICE[m]]['miss_rate']*100:.1f}" for m in models])
    return payload


if __name__ == "__main__":
    r = run()
    print(f"[aggregation_sensitivity] FP spread range {r['fp_spread_range_pp']} pp across "
          f"{len(r['policies'])} rules + {len(r['single_call_configurations'])} single-call configs; "
          f"deployable alert ratio {r['alert_ratio_range_deployable']}-fold; "
          f"cluster-permutation p={r['cluster_permutation']['p']}")
