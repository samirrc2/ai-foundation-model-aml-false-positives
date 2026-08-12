"""Mint the synthetic AML typology battery — deterministic, offline, $0.

Anchoring: FATF published typology catalogue + SAML-D / IBM AMLSim synthetic-AML
lineages. Cases are labelled suspicious/benign; benign cases are HARD NEGATIVES
(legitimate patterns that superficially resemble an alert). Transaction
sub-networks are serialized in a fixed node/edge plain-text schema following the
graph-serialization convention of arXiv 2507.14785 (cited precedent).

Determinism: everything is seeded from battery.yaml `seed`. The full battery is
minted once; the pilot battery is a strict stratified SUBSAMPLE (pilot ⊂ full).
Output is frozen to data/battery/*.jsonl and SHA-256'd into a manifest.

DUAL-USE: difficulty is a fixed design knob from FATF typology salience; no arm
tunes cases against model outputs. This is not an evasion catalogue.
"""
from __future__ import annotations
import argparse, hashlib, json, random, sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))
import loader as C  # noqa: E402

_HERE = Path(__file__).resolve().parent
_BATT = _HERE.parent / "data" / "battery"
_MANI = _HERE.parent / "manifest"

DIFFS = ("easy", "medium", "hard")
_BASE_DATE = date(2026, 1, 6)


# ── low-level deterministic helpers ─────────────────────────────────────────
def _rng(seed: int, *parts) -> random.Random:
    h = hashlib.sha256(("|".join([str(seed), *map(str, parts)])).encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _amt(r: random.Random, lo: int, hi: int, step: int = 10) -> int:
    return int(round(r.randint(lo, hi) / step) * step)


def _day(r: random.Random, span: int = 150) -> str:
    # H4: realistic temporal dispersion — irregular spacing across a wide window.
    return (_BASE_DATE + timedelta(days=r.randint(0, span))).isoformat()


def _irregular_subthreshold(r: random.Random) -> int:
    """H2: an irregular sub-$10k amount. Only a minority sit just under the CTR
    line; most are dispersed, mixed round and non-round. No uniform tell."""
    if r.random() < 0.30:
        return int(r.randint(9000, 9950))                 # minority just-under
    step = r.choice([1, 10, 50, 100])                     # single rounding factor
    return int(round(r.randint(1200, 8600) / step) * step)


def _acct(prefix: str, i: int) -> str:
    return f"{prefix}{i}"


# H3: benign background counterparties injected among the case accounts so the
# typology signal is interleaved with ordinary volume (no isolated-signal tell).
_BG_KINDS = [
    ("PAYROLL", "employer_ach", "payroll", 1800, 5200),
    ("VENDOR", "business_account", "invoice_payment", 400, 9000),
    ("UTILITY", "biller", "utility_bill", 60, 900),
    ("CARD", "card_acquirer", "card_settlement", 200, 4000),
    ("RENT", "property_mgr", "rent", 900, 3500),
    ("TAX", "tax_authority", "tax_payment", 300, 6000),
]


def _inject_background(r: random.Random, nodes: list[dict], edges: list[dict], diff: str) -> None:
    n_bg = {"easy": 2, "medium": 5, "hard": 9}[diff]
    acct_ids = [n["id"] for n in nodes
                if str(n.get("type", "")).endswith("account") or n.get("type") in (
                    "business_account", "personal_account", "corporate_treasury")]
    if not acct_ids:
        acct_ids = [nodes[0]["id"]]
    for i in range(n_bg):
        prefix, ntype, chan, lo, hi = r.choice(_BG_KINDS)
        cp = _acct(prefix, i + 1)
        nodes.append({"id": cp, "type": ntype})
        a = r.choice(acct_ids)
        inbound = r.random() < 0.5
        src, dst = (cp, a) if inbound else (a, cp)
        edges.append({"id": f"BG{i+1}", "src": src, "dst": dst,
                      "amount": _amt(r, lo, hi), "date": _day(r), "channel": chan})


# ── serialization (label-free, RAW LOGS ONLY — H1: no NL summary line) ───────
def serialize(nodes: list[dict], edges: list[dict]) -> str:
    lines = ["NODES:"]
    for n in nodes:
        attrs = " ".join(f"{k}={v}" for k, v in n.items() if k != "id")
        lines.append(f"  {n['id']}  {attrs}")
    lines.append("EDGES (transfers, USD):")
    for e in edges:
        lines.append(f"  {e['id']}  {e['src']} -> {e['dst']}  amount={e['amount']:,}"
                     f"  date={e['date']}  channel={e['channel']}")
    return "\n".join(lines)


# ── suspicious typology generators ──────────────────────────────────────────
def gen_structuring(r, diff):
    # sub-threshold cash deposits dodging the $10k CTR (H2: irregular amounts across
    # locations/dates, only a minority near the threshold — no uniform tell).
    n = {"easy": 9, "medium": 6, "hard": 4}[diff]
    tgt = {"id": "ACC1", "type": "personal_account", "kyc": "basic", "country": "US",
           "opened": 2025}
    nodes = [tgt]
    edges = []
    for i in range(n):
        src = _acct("CASH", i + 1)
        nodes.append({"id": src, "type": "cash_deposit", "location": r.choice(
            ["branch_A", "branch_B", "atm_7", "branch_C", "atm_2", "branch_E"])})
        edges.append({"id": f"E{i+1}", "src": src, "dst": "ACC1",
                      "amount": _irregular_subthreshold(r), "date": _day(r),
                      "channel": "cash"})
    return nodes, edges, ""


def gen_layering(r, diff):
    hops = {"easy": 6, "medium": 5, "hard": 4}[diff]
    nodes, edges = [], []
    amt = _amt(r, 45000, 90000)
    prev = "ORIG"
    nodes.append({"id": "ORIG", "type": "personal_account", "kyc": "verified", "country": "US"})
    for i in range(hops):
        nxt = _acct("H", i + 1)
        nodes.append({"id": nxt, "type": "personal_account", "kyc": r.choice(
            ["basic", "limited"]), "country": r.choice(["US", "CY", "AE", "PA"])})
        drop = 1.0 if diff == "hard" else r.choice([0.95, 0.9])
        amt = int(amt * drop)
        edges.append({"id": f"E{i+1}", "src": prev, "dst": nxt, "amount": amt,
                      "date": _day(r, 8), "channel": "wire",
                      "note": "same-day onward transfer" if diff != "hard" else ""})
        prev = nxt
    ctx = f"Funds traverse {hops} accounts across jurisdictions within days, near pass-through."
    return nodes, edges, ctx


def gen_trade_based(r, diff):
    goods = _amt(r, 100000, 300000, 1000)
    mult = {"easy": 3.0, "medium": 1.8, "hard": 1.35}[diff]
    paid = int(goods * mult)
    nodes = [
        {"id": "IMP", "type": "business_account", "kyc": "verified", "country": "US",
         "sector": "electronics_import"},
        {"id": "EXP", "type": "business_account", "kyc": "limited", "country": "HK",
         "sector": "trading"},
    ]
    edges = [{"id": "E1", "src": "IMP", "dst": "EXP", "amount": paid, "date": _day(r, 30),
              "channel": "wire", "note": f"invoice_states_goods={goods:,}"}]
    ctx = (f"Payment of {paid:,} against invoice for goods valued {goods:,} "
           f"(over-invoicing ratio {mult:g}x).")
    return nodes, edges, ctx


def gen_mule_network(r, diff):
    n = {"easy": 12, "medium": 8, "hard": 5}[diff]
    nodes = [{"id": "BEN", "type": "personal_account", "kyc": "basic", "country": "US",
              "opened": 2025}]
    edges = []
    for i in range(n):
        m = _acct("M", i + 1)
        nodes.append({"id": m, "type": "personal_account", "kyc": "basic",
                      "age_days": r.randint(3, 40)})
        edges.append({"id": f"E{i+1}", "src": m, "dst": "BEN",
                      "amount": _amt(r, 400, 1900), "date": _day(r, 10), "channel": "p2p",
                      "note": "newly-opened account" if diff != "hard" else ""})
    ctx = f"{n} recently-opened low-value accounts converge onto one beneficiary."
    return nodes, edges, ctx


def gen_shell_layering(r, diff):
    n = {"easy": 4, "medium": 3, "hard": 3}[diff]
    nodes = [{"id": "SRC", "type": "business_account", "kyc": "verified", "country": "US"}]
    edges = []
    prev = "SRC"
    amt = _amt(r, 60000, 200000, 1000)
    for i in range(n):
        s = _acct("SHELL", i + 1)
        nodes.append({"id": s, "type": "business_account", "incorporated": 2026,
                      "employees": 0, "country": r.choice(["BVI", "PA", "SC", "US"]),
                      "kyc": "limited"})
        edges.append({"id": f"E{i+1}", "src": prev, "dst": s, "amount": amt,
                      "date": _day(r, 15), "channel": "wire",
                      "note": "no-substance entity" if diff != "hard" else ""})
        prev = s
    ctx = f"Funds routed through {n} recently-incorporated no-employee shell entities."
    return nodes, edges, ctx


def gen_funnel_account(r, diff):
    n = {"easy": 10, "medium": 7, "hard": 5}[diff]
    nodes = [{"id": "FUNNEL", "type": "personal_account", "kyc": "basic", "country": "US"}]
    edges = []
    states = ["TX", "FL", "NY", "CA", "AZ", "GA", "NV", "IL", "WA", "NC"]
    for i in range(n):
        d = _acct("DEP", i + 1)
        nodes.append({"id": d, "type": "cash_deposit", "location": states[i % len(states)]})
        edges.append({"id": f"D{i+1}", "src": d, "dst": "FUNNEL",
                      "amount": _amt(r, 1500, 4500), "date": _day(r, 6), "channel": "cash"})
    edges.append({"id": "W1", "src": "FUNNEL", "dst": "OUT",
                  "amount": sum(e["amount"] for e in edges), "date": _day(r, 3),
                  "channel": "wire", "note": "single-location withdrawal"})
    nodes.append({"id": "OUT", "type": "business_account", "country": "US"})
    ctx = f"Deposits across {n} states, aggregated and withdrawn in one location."
    return nodes, edges, ctx


def gen_rapid_passthrough(r, diff):
    amt = _amt(r, 30000, 120000, 500)
    keep = {"easy": 0.0, "medium": 0.03, "hard": 0.08}[diff]
    nodes = [
        {"id": "IN", "type": "personal_account", "country": r.choice(["RU", "NG", "US"])},
        {"id": "PASS", "type": "personal_account", "kyc": "basic", "country": "US"},
        {"id": "OUT", "type": "business_account", "country": r.choice(["AE", "CN", "US"])},
    ]
    d = _day(r, 1)
    edges = [
        {"id": "E1", "src": "IN", "dst": "PASS", "amount": amt, "date": d, "channel": "wire"},
        {"id": "E2", "src": "PASS", "dst": "OUT", "amount": int(amt * (1 - keep)),
         "date": d, "channel": "wire", "note": "same-day out" if diff != "hard" else ""},
    ]
    ctx = f"Funds in and out same day; ~{keep*100:.0f}% retained (pass-through)."
    return nodes, edges, ctx


def gen_cash_intensive_front(r, diff):
    plausible = _amt(r, 8000, 20000, 100)
    mult = {"easy": 5.0, "medium": 2.6, "hard": 1.7}[diff]
    declared = int(plausible * mult)
    nodes = [{"id": "BIZ", "type": "business_account", "sector": "restaurant",
              "kyc": "verified", "country": "US", "declared_weekly_revenue": plausible}]
    edges = []
    for i in range(5):
        edges.append({"id": f"C{i+1}", "src": _acct("TILL", i + 1), "dst": "BIZ",
                      "amount": _amt(r, declared // 6, declared // 4),
                      "date": _day(r, 30), "channel": "cash"})
    for i in range(5):
        nodes.append({"id": _acct("TILL", i + 1), "type": "cash_deposit"})
    ctx = (f"Cash deposits imply ~{declared:,}/wk vs declared {plausible:,}/wk "
           f"({mult:g}x plausible revenue).")
    return nodes, edges, ctx


# ── benign hard-negative generators ─────────────────────────────────────────
def gen_payroll_fanout(r, diff):
    n = {"easy": 8, "medium": 10, "hard": 14}[diff]
    nodes = [{"id": "EMPLOYER", "type": "business_account", "kyc": "verified",
              "country": "US", "sector": "verified_employer", "payroll_provider": "ADP"}]
    edges = []
    for i in range(n):
        e = _acct("EMP", i + 1)
        nodes.append({"id": e, "type": "personal_account", "kyc": "verified",
                      "tenure_months": r.randint(6, 60)})
        edges.append({"id": f"P{i+1}", "src": "EMPLOYER", "dst": e,
                      "amount": _amt(r, 2200, 5200), "date": "2026-03-15",
                      "channel": "ach", "note": "scheduled_payroll"})
    ctx = f"Verified employer disburses semi-monthly payroll to {n} tenured employees via ADP."
    return nodes, edges, ctx


def gen_treasury_sweep(r, diff):
    n = 4
    nodes = [{"id": "HQ", "type": "corporate_treasury", "kyc": "verified", "country": "US",
              "group": "same_parent"}]
    edges = []
    for i in range(n):
        s = _acct("SUB", i + 1)
        nodes.append({"id": s, "type": "business_account", "group": "same_parent",
                      "kyc": "verified"})
        edges.append({"id": f"S{i+1}", "src": s, "dst": "HQ", "amount": _amt(r, 50000, 400000, 1000),
                      "date": "2026-03-31", "channel": "book_transfer",
                      "note": "intragroup_zero_balancing"})
    ctx = "Month-end zero-balancing sweep of subsidiary cash to parent treasury (same group)."
    return nodes, edges, ctx


def gen_genuine_trade_finance(r, diff):
    goods = _amt(r, 100000, 300000, 1000)
    nodes = [
        {"id": "BUYER", "type": "business_account", "kyc": "verified", "country": "US"},
        {"id": "SELLER", "type": "business_account", "kyc": "verified", "country": "DE"},
        {"id": "BANK", "type": "issuing_bank", "instrument": "letter_of_credit"},
    ]
    edges = [{"id": "E1", "src": "BUYER", "dst": "SELLER", "amount": goods,
              "date": _day(r, 30), "channel": "wire",
              "note": "LC_backed;BoL+invoice_match"}]
    ctx = f"LC-backed payment {goods:,} matching bill of lading and commercial invoice."
    return nodes, edges, ctx


def gen_retail_settlement(r, diff):
    nodes = [{"id": "MERCHANT", "type": "business_account", "kyc": "verified",
              "sector": "grocery_chain", "country": "US"}]
    edges = []
    for i in range(6):
        edges.append({"id": f"R{i+1}", "src": "ACQUIRER", "dst": "MERCHANT",
                      "amount": _amt(r, 40000, 120000, 100), "date": _day(r, 30),
                      "channel": "card_settlement", "note": "daily_batch"})
    nodes.append({"id": "ACQUIRER", "type": "card_acquirer", "kyc": "verified"})
    ctx = "High-volume daily card-acquirer settlements to an established grocery chain."
    return nodes, edges, ctx


def gen_marketplace_payouts(r, diff):
    n = {"easy": 8, "medium": 10, "hard": 13}[diff]
    nodes = [{"id": "PLATFORM", "type": "business_account", "kyc": "verified",
              "sector": "marketplace", "country": "US"}]
    edges = []
    for i in range(n):
        s = _acct("SELLER", i + 1)
        nodes.append({"id": s, "type": "business_account", "kyc": "verified",
                      "seller_rating": r.choice(["4.6", "4.8", "4.9"])})
        edges.append({"id": f"O{i+1}", "src": "PLATFORM", "dst": s,
                      "amount": _amt(r, 300, 3000), "date": _day(r, 14),
                      "channel": "ach", "note": "weekly_seller_payout"})
    ctx = f"Licensed marketplace pays {n} rated sellers their weekly balances."
    return nodes, edges, ctx


def gen_loan_disbursement(r, diff):
    amt = _amt(r, 40000, 150000, 500)
    nodes = [
        {"id": "LENDER", "type": "bank", "kyc": "verified", "country": "US"},
        {"id": "BORROWER", "type": "business_account", "kyc": "verified"},
        {"id": "VENDOR", "type": "business_account", "kyc": "verified", "sector": "equipment"},
    ]
    edges = [
        {"id": "E1", "src": "LENDER", "dst": "BORROWER", "amount": amt, "date": _day(r, 10),
         "channel": "wire", "note": "approved_equipment_loan"},
        {"id": "E2", "src": "BORROWER", "dst": "VENDOR", "amount": amt, "date": _day(r, 12),
         "channel": "wire", "note": "equipment_purchase_invoiced"},
    ]
    ctx = "Approved equipment loan disbursed then paid to an invoiced vendor."
    return nodes, edges, ctx


def gen_remittance_corridor(r, diff):
    n = {"easy": 6, "medium": 8, "hard": 11}[diff]
    nodes = [{"id": "MTO", "type": "licensed_money_transmitter", "kyc": "verified",
              "country": "US", "license": "FinCEN_MSB"}]
    edges = []
    for i in range(n):
        s = _acct("SENDER", i + 1)
        nodes.append({"id": s, "type": "personal_account", "kyc": "verified"})
        edges.append({"id": f"T{i+1}", "src": s, "dst": "MTO",
                      "amount": _amt(r, 150, 900), "date": _day(r, 20),
                      "channel": "remittance", "note": "family_support_PH"})
    ctx = f"Licensed MSB aggregates {n} small documented family remittances on a corridor."
    return nodes, edges, ctx


def gen_subscription_billing(r, diff):
    n = {"easy": 8, "medium": 12, "hard": 16}[diff]
    nodes = [{"id": "SAAS", "type": "business_account", "kyc": "verified",
              "sector": "software", "country": "US"}]
    edges = []
    for i in range(n):
        c = _acct("CUST", i + 1)
        nodes.append({"id": c, "type": "personal_account", "kyc": "verified"})
        edges.append({"id": f"B{i+1}", "src": c, "dst": "SAAS",
                      "amount": r.choice([9, 19, 29, 49]), "date": _day(r, 30),
                      "channel": "card", "note": "recurring_subscription"})
    ctx = f"{n} small recurring subscription charges inbound to an established SaaS vendor."
    return nodes, edges, ctx


SUSPICIOUS_GENS = {
    "structuring": gen_structuring, "layering": gen_layering,
    "trade_based": gen_trade_based, "mule_network": gen_mule_network,
    "shell_layering": gen_shell_layering, "funnel_account": gen_funnel_account,
    "rapid_passthrough": gen_rapid_passthrough, "cash_intensive_front": gen_cash_intensive_front,
}
BENIGN_GENS = {
    "payroll_fanout": gen_payroll_fanout, "treasury_sweep": gen_treasury_sweep,
    "genuine_trade_finance": gen_genuine_trade_finance, "retail_settlement": gen_retail_settlement,
    "marketplace_payouts": gen_marketplace_payouts, "loan_disbursement": gen_loan_disbursement,
    "remittance_corridor": gen_remittance_corridor, "subscription_billing": gen_subscription_billing,
}


# ── stratified minting ──────────────────────────────────────────────────────
def _counts(total: int, keys: list[str], mix: dict[str, float], seed: int, tag: str):
    """Split `total` cases across keys x difficulties, deterministically, so the
    per-stratum counts sum exactly to `total`."""
    per_key = [total // len(keys)] * len(keys)
    for i in range(total - sum(per_key)):
        per_key[i] += 1
    out = {}
    for k, nk in zip(keys, per_key):
        dc = {d: int(nk * mix[d]) for d in DIFFS}
        rem = nk - sum(dc.values())
        for d in list(DIFFS)[:rem]:
            dc[d] += 1
        out[k] = dc
    return out


def build_case(kind: str, key: str, diff: str, idx: int, seed: int) -> dict:
    r = _rng(seed, kind, key, diff, idx)
    gen = (SUSPICIOUS_GENS if kind == "suspicious" else BENIGN_GENS)[key]
    nodes, edges, _ctx = gen(r, diff)              # H1: NL summary discarded
    _inject_background(r, nodes, edges, diff)      # H3: interleave benign volume
    # H3/H4: present as a single chronological ledger so the typology signal is
    # interleaved with background volume rather than appearing first in isolation.
    edges.sort(key=lambda e: (e["date"], e["id"]))
    for i, e in enumerate(edges, 1):
        e["id"] = f"T{i}"
    prefix = "S" if kind == "suspicious" else "B"
    case_id = f"{prefix}-{key}-{diff[:1]}-{idx:03d}"
    body = serialize(nodes, edges)
    return {
        "case_id": case_id,
        "label": kind,                                   # suspicious | benign
        "typology": key if kind == "suspicious" else None,
        "benign_pattern": key if kind == "benign" else None,
        "difficulty": diff,
        "stratum": f"{kind}:{key}",                       # clustering unit = typology/pattern
        "n_nodes": len(nodes), "n_edges": len(edges),
        "serialized": body,
        "content_sha256": hashlib.sha256(body.encode()).hexdigest(),
    }


def mint_full(cfg) -> list[dict]:
    b = cfg.battery
    seed = b.seed
    total = b.sizes.full
    n_susp = int(round(total * b.class_balance["suspicious"]))
    n_ben = total - n_susp
    susp_counts = _counts(n_susp, list(SUSPICIOUS_GENS), b.difficulty_mix, seed, "susp")
    ben_counts = _counts(n_ben, list(BENIGN_GENS), b.difficulty_mix, seed, "ben")
    cases = []
    for key, dc in susp_counts.items():
        for diff, n in dc.items():
            for i in range(n):
                cases.append(build_case("suspicious", key, diff, i, seed))
    for key, dc in ben_counts.items():
        for diff, n in dc.items():
            for i in range(n):
                cases.append(build_case("benign", key, diff, i, seed))
    cases.sort(key=lambda c: c["case_id"])
    return cases


def subsample_pilot(cfg, full: list[dict]) -> list[dict]:
    """Strict stratified subsample: pilot ⊂ full, proportional per stratum×difficulty."""
    b = cfg.battery
    want = b.sizes.pilot
    frac = want / len(full)
    by = {}
    for c in full:
        by.setdefault((c["stratum"], c["difficulty"]), []).append(c)
    chosen = []
    for k in sorted(by):
        grp = sorted(by[k], key=lambda c: c["case_id"])
        take = max(1, int(round(len(grp) * frac)))
        r = _rng(b.seed, "pilot", *k)
        chosen.extend(r.sample(grp, min(take, len(grp))))
    # trim/pad deterministically to hit exactly `want`
    chosen.sort(key=lambda c: c["case_id"])
    if len(chosen) > want:
        r = _rng(b.seed, "pilot_trim")
        drop = set(r.sample(range(len(chosen)), len(chosen) - want))
        chosen = [c for i, c in enumerate(chosen) if i not in drop]
    elif len(chosen) < want:
        pool = [c for c in full if c["case_id"] not in {x["case_id"] for x in chosen}]
        r = _rng(b.seed, "pilot_pad")
        chosen.extend(r.sample(pool, want - len(chosen)))
    chosen.sort(key=lambda c: c["case_id"])
    return chosen


def _write(cases: list[dict], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(cases: list[dict]) -> dict:
    from collections import Counter
    return {
        "n": len(cases),
        "by_label": dict(Counter(c["label"] for c in cases)),
        "by_stratum": dict(Counter(c["stratum"] for c in cases)),
        "by_difficulty": dict(Counter(c["difficulty"] for c in cases)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["full", "pilot", "both"], default="both")
    args = ap.parse_args()

    cfg = C.load_all()
    full = mint_full(cfg)
    pilot = subsample_pilot(cfg, full)

    _MANI.mkdir(parents=True, exist_ok=True)
    receipts = {"config_hash": cfg.config_hash(), "seed": cfg.battery.seed}

    if args.which in ("full", "both"):
        h = _write(full, _BATT / "full.jsonl")
        receipts["full"] = {"sha256": h, **_summary(full)}
        print(f"[battery] full : {len(full)} cases  sha256={h[:16]}...")
    if args.which in ("pilot", "both"):
        h = _write(pilot, _BATT / "pilot.jsonl")
        receipts["pilot"] = {"sha256": h, **_summary(pilot)}
        print(f"[battery] pilot: {len(pilot)} cases  sha256={h[:16]}...")

    (_MANI / "battery_manifest.json").write_text(json.dumps(receipts, indent=2, sort_keys=True))
    print(f"[battery] manifest -> manifest/battery_manifest.json")
    return 0


def load_battery(which: str) -> list[dict]:
    path = _BATT / f"{which}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run capture/build_battery.py first")
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


if __name__ == "__main__":
    sys.exit(main())
