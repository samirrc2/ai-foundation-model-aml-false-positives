"""Non-LLM baselines on the SAME frozen 600-case battery — a reference frame so the
LLM operating points can be located relative to what banks already run. Pure, $0.

Two baselines:
  (1) RULES — hand-coded FATF red-flag heuristics (NOT trained on labels): the kind
      of deterministic typology rules a legacy transaction-monitoring system encodes.
  (2) SUPERVISED — a simple classifier (logistic regression + gradient boosting) on
      engineered graph features, evaluated with 5-fold stratified out-of-fold
      predictions. On a synthetic battery whose structure encodes the typologies this
      is an OPTIMISTIC ceiling (the features can recover the generator), so it is
      reported as a best-case reference, not a real-world performance claim.

Reports per-baseline false-positive rate (benign flagged) and miss rate (suspicious
not flagged), for direct comparison with the LLM table.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BATT = _HERE.parent / "data" / "battery" / "full.jsonl"

_HIGH_RISK = {"RU", "NG", "PA", "BVI", "SC", "CY", "AE", "HK", "CN"}
_EDGE = re.compile(r"->\s+(\S+)\s+amount=([\d,]+)\s+date=(\S+)\s+channel=(\w+)")


def load_cases():
    return [json.loads(l) for l in _BATT.read_text().splitlines() if l.strip()]


# ── feature extraction from the serialized ledger ───────────────────────────
def features(case: dict) -> dict:
    text = case["serialized"]
    nodes_blk = text.split("NODES:")[1].split("EDGES")[0]
    edges = _EDGE.findall(text)
    amts = [int(a.replace(",", "")) for _dst, a, _d, _c in edges]
    dates = sorted({d for _dst, _a, d, _c in edges})
    channels = [c for *_x, c in edges]
    dsts = [d for d, *_x in edges]
    from collections import Counter
    dstc = Counter(dsts)
    top_fanin = max(dstc.values()) if dstc else 0
    span = 0
    if len(dates) >= 2:
        from datetime import date
        ds = [date.fromisoformat(d) for d in dates]
        span = (max(ds) - min(ds)).days
    return {
        "n_nodes": case["n_nodes"], "n_edges": case["n_edges"],
        "n_cash": channels.count("cash"),
        "max_amt": max(amts) if amts else 0,
        "total_amt": sum(amts),
        "n_sub10k": sum(1 for a in amts if 1000 <= a < 10000),
        "n_justunder": sum(1 for a in amts if 8500 <= a < 10000),
        "top_fanin": top_fanin,
        "n_wire": channels.count("wire"),
        "n_shell": nodes_blk.count("employees=0") + nodes_blk.count("incorporated=2026"),
        "n_highrisk": sum(nodes_blk.count(f"country={c}") for c in _HIGH_RISK),
        "n_limited_kyc": nodes_blk.count("kyc=limited") + nodes_blk.count("kyc=basic"),
        "date_span": span,
        "n_dates": len(dates),
    }


# ── (1) rules baseline — FATF red-flag heuristics, no training ───────────────
def rules_flag(f: dict) -> bool:
    # structuring / funnel: multiple sub-threshold cash-in to one beneficiary
    if f["n_cash"] >= 3 and f["n_sub10k"] >= 3 and f["top_fanin"] >= 3:
        return True
    # mule: many low-value senders converge
    if f["top_fanin"] >= 5 and f["max_amt"] <= 5000:
        return True
    # shell layering: no-substance entities present in a wire chain
    if f["n_shell"] >= 1 and f["n_wire"] >= 1:
        return True
    # high-risk jurisdiction wires with limited KYC
    if f["n_highrisk"] >= 1 and f["n_wire"] >= 1 and f["n_limited_kyc"] >= 1:
        return True
    # rapid pass-through: large wire in and out within a day
    if f["date_span"] <= 1 and f["n_wire"] >= 2 and f["max_amt"] >= 20000:
        return True
    return False


def _rates(cases, pred):
    """pred: case_id -> bool flagged. Returns (fp_rate, miss_rate)."""
    ben = [c for c in cases if c["label"] == "benign"]
    sus = [c for c in cases if c["label"] == "suspicious"]
    fp = sum(1 for c in ben if pred[c["case_id"]]) / len(ben)
    miss = sum(1 for c in sus if not pred[c["case_id"]]) / len(sus)
    return fp, miss


def run_rules(cases):
    pred = {c["case_id"]: rules_flag(features(c)) for c in cases}
    return _rates(cases, pred)


# ── (2) supervised baseline — stratified 5-fold out-of-fold ─────────────────
def run_supervised(cases, seed=4242):
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler
    feat_names = list(features(cases[0]).keys())
    X = np.array([[features(c)[k] for k in feat_names] for c in cases], dtype=float)
    y = np.array([1 if c["label"] == "suspicious" else 0 for c in cases])
    ids = [c["case_id"] for c in cases]
    out = {}
    for name, mk in (("logistic", lambda: LogisticRegression(max_iter=1000, C=1.0)),
                     ("grad_boost", lambda: GradientBoostingClassifier(random_state=seed))):
        oof = {}
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for tr, te in skf.split(X, y):
            sc = StandardScaler().fit(X[tr])
            clf = mk().fit(sc.transform(X[tr]), y[tr])
            pr = clf.predict(sc.transform(X[te]))
            for j, idx in enumerate(te):
                oof[ids[idx]] = bool(pr[j])
        out[name] = _rates(cases, oof)
    return out


def main():
    cases = load_cases()
    print(f"[baselines] battery: {len(cases)} cases "
          f"({sum(c['label']=='benign' for c in cases)} benign / "
          f"{sum(c['label']=='suspicious' for c in cases)} suspicious)\n")
    fp, miss = run_rules(cases)
    print(f"  {'RULES (FATF heuristics)':28s} FP={fp:6.1%}  miss={miss:6.1%}")
    for name, (fp, miss) in run_supervised(cases).items():
        print(f"  {'SUPERVISED ('+name+')':28s} FP={fp:6.1%}  miss={miss:6.1%}")
    print("\n  (supervised = 5-fold out-of-fold; optimistic ceiling on synthetic "
          "structure — see module docstring)")


if __name__ == "__main__":
    sys.exit(main())
