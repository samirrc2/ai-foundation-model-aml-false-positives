"""Capture orchestrator — perishable, impure, resumable, ledger-gated.

Captures ONE (model, prompt_variant) over a battery subgrid into an immutable
append-only CSV data/raw/runs_<model>_<variant>.csv. The unit is one screening
cell = (seed_index, case). The per-cell seed is derived from (master, case_id,
variant, seed_index) so EVERY model sees identical seeds at a matched cell — the
model is the only thing that differs, which is what lets cross-model miss
correlation be attributed to the models.

Budget: a persisted global Ledger enforces the cap across ALL invocations of a
run (so capturing model-by-model still cannot cross $10 in aggregate). API calls
happen OUTSIDE the lock; ledger mutation + CSV append happen INSIDE the lock.
Worst-case cost is reserved before each call, so the cap is safe under concurrency;
the pool drains in-flight on breach. On resume, completed cells are skipped and
never re-billed. ERROR is a first-class label, never coerced to a flag/miss.

Usage:
  PILOT_MOCK=1 python capture/orchestrator.py --subgrid pilot --model openai_4o_mini --variant v_terse
  python capture/orchestrator.py --subgrid pilot --model gemini_flash --variant v_fatf --concurrency 5
"""
from __future__ import annotations
import argparse, csv, hashlib, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "config"))

import agent as agentmod          # noqa: E402
import secrets as secretstore     # noqa: E402
import ledger as ledgermod        # noqa: E402
import loader as C                # noqa: E402
from build_battery import load_battery  # noqa: E402

_HERE = Path(__file__).resolve().parent
_RAW = _HERE.parent / "data" / "raw"
_MANI = _HERE.parent / "manifest"

CSV_FIELDS = [
    "subgrid", "mode", "model_key", "api_model", "provider", "family",
    "prompt_variant", "seed_index", "case_id", "label", "typology", "difficulty",
    "stratum", "seed", "temperature", "timestamp_utc", "prompt_hash",
    "content_sha256", "suspicious", "decision", "out_typology", "rationale",
    "input_tokens", "output_tokens", "cost_usd", "ok", "error", "key_id",
    "raw_response",
]


def cell_seed(master: int, case_id: str, variant: str, seed_index: int) -> int:
    raw = f"{master}|{case_id}|{variant}|{seed_index}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def load_done(path: Path) -> set:
    done = set()
    if path.exists():
        for r in csv.DictReader(path.open()):
            if r.get("ok") == "True":
                done.add((int(r["seed_index"]), r["case_id"]))
    return done


def detect_mock(path: Path):
    if not path.exists():
        return None
    try:
        with path.open() as f:
            row = next(csv.DictReader(f))
        return row.get("mode", "").upper() == "MOCK"
    except Exception:
        return None


def classify_error(err: str):
    e = (err or ""); el = e.lower()
    delay = None
    m = re.search(r"retry.?after['\":\s]+(\d+(?:\.\d+)?)", el) or \
        re.search(r"retrydelay['\":\s]+(\d+(?:\.\d+)?)s", el)
    if m:
        delay = float(m.group(1))
    # DAILY quota (requests-per-day) — won't recover within the run; halt the stream
    # cleanly and resume after the daily reset (resumable, no re-bill).
    if any(k in el for k in ("per day", "per-day", "requests_per_day", "(rpd)", " rpd",
                             "requests per day", "tokens per day", "(tpd)")):
        return "quota_daily", delay
    # TERMINAL account block (out of credits / spending limit / permission denied) —
    # no retry can fix it; stop this provider's stream cleanly.
    if any(k in el for k in ("spending limit", "purchase more credits", "permission-denied",
                             "permission denied", "billing", "insufficient_quota",
                             "used all available credits")):
        return "account_dead", delay
    # all keys cooling down → treat as a (longer) rate-limit wait, then retry
    if "cooling down" in el or ("keys" in el and "rate-limited" in el) \
            or ("all" in el and "keys benched" in el):
        return "exhausted", delay
    if "429" in e or "rate limit" in el or "rate_limit" in el or "rate-limited" in el \
            or "quota" in el or "resource_exhausted" in el:
        return "rate_limit", delay
    if any(k in el for k in ("timeout", "timed out", "connection", "503", "502",
                             "unavailable", "reset")):
        return "transient", delay
    return "other", delay


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subgrid", default="pilot")
    ap.add_argument("--model", required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--spend-cap", type=float, default=None)
    ap.add_argument("--ledger-suffix", default="",
                    help="separate ledger file per parallel stream, e.g. _openai")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = C.load_all()
    grid = cfg.grid
    sg = C.subgrid(cfg, args.subgrid)
    if args.model not in sg.models:
        print(f"[capture] ERROR: model {args.model!r} not in subgrid {args.subgrid!r} "
              f"({sg.models})"); return 2
    if args.variant not in sg.variants:
        print(f"[capture] ERROR: variant {args.variant!r} not in subgrid {args.subgrid!r} "
              f"({sg.variants})"); return 2

    mcfg = cfg.models.cfg(args.model).model_dump()
    provider = mcfg["provider"]
    master = int(grid.seed_master)
    temp = float(grid.judge_temperature)
    max_retries = int(grid.max_retries)
    workers = max(1, args.concurrency or int(grid.max_workers))

    mock = os.environ.get("PILOT_MOCK") == "1"
    mode = "MOCK" if mock else "REAL"
    rpm = 0 if mock else (grid.rpm_limits or {}).get(provider, 0)  # no throttle offline
    cap = args.spend_cap if args.spend_cap is not None else float(
        getattr(grid.budgets, args.subgrid, grid.budgets.pilot))
    margin = float(grid.stop_margin_usd)

    cases = load_battery(sg.battery)
    cells = [(si, c) for si in sg.seed_indices for c in cases]

    _RAW.mkdir(parents=True, exist_ok=True)
    out_csv = _RAW / f"runs_{args.subgrid}_{args.model}_{args.variant}.csv"

    if out_csv.exists():
        if not os.access(out_csv, os.W_OK):
            print(f"[capture] REFUSING: {out_csv.name} is read-only (frozen). "
                  f"chmod +w or remove to re-capture."); return 4
        prior = detect_mock(out_csv)
        if prior is not None and prior != mock:
            print(f"[capture] REFUSING: {out_csv.name} holds "
                  f"{'MOCK' if prior else 'REAL'} rows but this is a {mode} run."); return 5

    # global persisted ledger (shared across all model/variant invocations of the run)
    led = ledgermod.Ledger.load(
        _MANI / f"ledger_{args.subgrid}_{mode}{args.ledger_suffix}.json", cap, margin)
    wc = ledgermod.worst_case_cost(mcfg)   # real worst-case (exercises reserve/preflight)
    # MOCK is offline: no vendor call, so REAL spend is $0. We keep real prices for the
    # reservation/preflight math but BILL $0 in mock so the ledger truthfully reads $0.
    bill_in = 0.0 if mock else mcfg["price_in"]
    bill_out = 0.0 if mock else mcfg["price_out"]

    done = load_done(out_csv)
    todo = [(si, c) for (si, c) in cells if (si, c["case_id"]) not in done]

    # pre-flight budget refusal (projected worst-case of THIS invocation + already spent)
    ok, projected_total = led.preflight_ok(wc * len(todo))
    print(f"[capture] {args.model}/{args.variant} ({mode}) subgrid={args.subgrid} "
          f"battery={sg.battery}")
    print(f"[capture] cells: {len(cells)} ({len(sg.seed_indices)} seeds x {len(cases)} cases); "
          f"{len(done)} done, {len(todo)} todo | workers={workers} rpm[{provider}]={rpm or 'none'}")
    print(f"[capture] ledger: spent ${led.cum_usd:.4f} / cap ${cap:.2f} | "
          f"worst-case this run ${wc*len(todo):.4f} | projected total ${projected_total:.4f}")
    if not ok:
        print(f"[capture] PREFLIGHT REFUSAL: projected ${projected_total:.4f} > "
              f"cap-margin ${cap - margin:.2f}. Not starting."); return 6
    if args.dry_run:
        print("[capture] DRY RUN ok."); return 0
    if not mock and not secretstore.get_pool(provider):
        print(f"[capture] ERROR: no usable key for provider {provider!r}."); return 2

    # rate limiter
    min_interval = (60.0 / rpm) if rpm and rpm > 0 else 0.0
    rl_lock = threading.Lock(); rl_next = [0.0]

    def throttle():
        if min_interval <= 0:
            return
        with rl_lock:
            now = time.monotonic(); t = max(now, rl_next[0]); rl_next[0] = t + min_interval
            wait = t - now
        if wait > 0:
            time.sleep(wait)

    new_file = (not out_csv.exists()) or out_csv.stat().st_size == 0
    fh = out_csv.open("a", newline="")
    writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
    if new_file:
        writer.writeheader()

    st = {"n_ok": 0, "n_err": 0, "n_done": 0, "stop": False, "daily_capped": False}
    io_lock = threading.Lock()
    total = len(todo)

    def write_row(si, case, seed, res):
        cost = ledgermod.price_of(bill_in, bill_out,
                                  res.input_tokens, res.output_tokens)
        decision = ("flag" if (res.ok and res.verdict.suspicious)
                    else ("no_flag" if res.ok else "ERROR"))
        csha = hashlib.sha256((res.raw_response or "").encode()).hexdigest()
        with io_lock:
            writer.writerow({
                "subgrid": args.subgrid, "mode": mode, "model_key": args.model,
                "api_model": mcfg["api_model"], "provider": provider, "family": mcfg["family"],
                "prompt_variant": args.variant, "seed_index": si, "case_id": case["case_id"],
                "label": case["label"], "typology": case.get("typology") or "",
                "difficulty": case["difficulty"], "stratum": case["stratum"],
                "seed": seed, "temperature": temp,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "prompt_hash": res.prompt_hash, "content_sha256": csha,
                "suspicious": (res.verdict.suspicious if res.ok else ""),
                "decision": decision,
                "out_typology": (res.verdict.typology or "" if res.ok else ""),
                "rationale": (res.verdict.rationale if res.ok else ""),
                "input_tokens": res.input_tokens, "output_tokens": res.output_tokens,
                "cost_usd": round(cost, 6), "ok": res.ok, "error": res.error or "",
                "key_id": res.key_id,
                "raw_response": (res.raw_response or "").replace("\n", " ")[:1500],
            })
            st["n_done"] += 1
            st["n_ok" if res.ok else "n_err"] += 1
            # Flush in batches: per-row fsync to a network mount is the throughput
            # bottleneck. Batching keeps the append resumable while staying fast.
            if st["n_done"] % 20 == 0 or st["n_done"] == total:
                fh.flush()
            if st["n_done"] % 100 == 0 or st["n_done"] == total:
                pct = 100.0 * st["n_done"] / total if total else 0.0
                print(f"  ...{st['n_done']}/{total} ({pct:.0f}%), "
                      f"${led.cum_usd:.4f} spent, {st['n_err']} err")

    def process(cell):
        si, case = cell
        if st["stop"]:
            return
        seed = cell_seed(master, case["case_id"], args.variant, si)
        if not led.reserve(wc):                # cap would be crossed → stop
            st["stop"] = True
            return
        try:
            for attempt in range(1, max_retries + 2):
                throttle()
                res = agentmod.run_agent(mcfg, case, args.variant, temp, seed)
                if res.ok:
                    led.commit(args.model, bill_in, bill_out,
                               res.input_tokens, res.output_tokens, wc)
                    write_row(si, case, seed, res)
                    return
                # failed call: bill any tokens spent, classify
                led.commit(args.model, bill_in, bill_out,
                           res.input_tokens, res.output_tokens, 0.0)
                kind, delay = classify_error(res.error)
                if kind == "quota_daily":
                    st["stop"] = True; st["daily_capped"] = True   # per-model daily cap
                    write_row(si, case, seed, res)
                    with io_lock:
                        print(f"  !! {args.model}: DAILY request/token limit reached "
                              f"(RPD/TPD). Halting this stream — re-run WITHOUT RESET "
                              f"after the daily reset to resume (no re-bill). ({res.error[:70]})")
                    return
                if kind == "account_dead":
                    st["stop"] = True                      # terminal: halt this stream
                    write_row(si, case, seed, res)
                    with io_lock:
                        print(f"  !! {args.model}: provider account out of credits / "
                              f"spending limit — halting this stream. Add credits and "
                              f"re-run to resume. ({res.error[:80]})")
                    return
                if kind in ("rate_limit", "transient", "exhausted") and attempt <= max_retries:
                    if kind == "exhausted":
                        wait = delay or 32.0          # let keys finish cooling down
                    elif kind == "rate_limit":
                        wait = delay or 2.0
                    else:
                        wait = 0.4 * (2 ** (attempt - 1))
                    time.sleep(min(45.0, wait))
                    continue
                write_row(si, case, seed, res)          # ERROR is first-class
                with io_lock:
                    print(f"  ! {case['case_id']} s{si} attempt {attempt} ERROR: {res.error}")
                return
        finally:
            led.release(wc)

    try:
        if workers == 1:
            for cell in todo:
                if st["stop"]:
                    break
                process(cell)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                list(ex.map(process, todo))
    finally:
        fh.close()
        led.save()

    err_rate = st["n_err"] / max(1, st["n_done"])
    if st["daily_capped"]:
        print(f"[capture] STOP: {args.model} hit its per-model DAILY limit "
              f"(spent ${led.cum_usd:.4f}). Other models may still have quota; the "
              f"runner will move on. Resume this model after the daily reset.")
    elif st["stop"]:
        print(f"[capture] STOP: spend cap ${cap:.2f} guard tripped "
              f"(spent ${led.cum_usd:.4f}). Resume by re-running.")
    print(f"[capture] done: {st['n_ok']} ok, {st['n_err']} ERROR "
          f"({err_rate*100:.2f}%), spend ${led.cum_usd:.4f} -> {out_csv.name}")
    if err_rate > 0.02:
        print(f"[capture] WARNING: ERROR rate {err_rate*100:.2f}% > 2% — "
              f"capture NON-AUTHORITATIVE until re-run to <=2%.")
    if not st["stop"] and st["n_done"] == total:
        print(f"[capture] next: python capture/freeze.py --subgrid {args.subgrid} "
              f"--model {args.model} --variant {args.variant}")
    if st["daily_capped"]:
        return 8                       # per-model daily cap: skip this model, keep going
    return 3 if st["stop"] else 0


if __name__ == "__main__":
    sys.exit(main())
