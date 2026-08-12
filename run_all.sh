#!/usr/bin/env bash
# P4 end-to-end runner.
#   SUBGRID=pilot|full   which grid (default pilot)
#   PILOT_MOCK=1         offline deterministic fake screener, $0 (default 0 = live)
#   CONC=N               worker concurrency (default 5)
#
# Pipeline: build battery -> capture each (model,variant), freeze on landing ->
# analysis (frozen only) -> pilot verdict. The ledger enforces the budget cap
# GLOBALLY across all captures; a budget stop aborts before freezing that CSV.
#
#   PILOT_MOCK=1 ./run_all.sh                 # offline dry-run (validate for $0)
#   ./run_all.sh                              # real pilot (<=$10, ledger-gated)
#   SUBGRID=full CONC=5 ./run_all.sh          # full run (ONLY after PILOT: PASS + go-ahead)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-python3}"
SUBGRID="${SUBGRID:-pilot}"
CONC="${CONC:-5}"
MOCK="${PILOT_MOCK:-0}"
MODE=$([ "$MOCK" = "1" ] && echo MOCK || echo REAL)

echo "== P4 run_all: subgrid=$SUBGRID mode=$MODE conc=$CONC =="

# 1. battery (deterministic, offline, $0)
if [ ! -f "data/battery/${SUBGRID}.jsonl" ]; then
  $PY capture/build_battery.py
fi

MODELS=$($PY -c "import sys;sys.path.insert(0,'config');import loader as C;print(' '.join(C.subgrid(C.load_all(),'$SUBGRID').models))")
VARIANTS=$($PY -c "import sys;sys.path.insert(0,'config');import loader as C;print(' '.join(C.subgrid(C.load_all(),'$SUBGRID').variants))")
echo "   models  : $MODELS"
echo "   variants: $VARIANTS"

# RESET=1 clears prior raw CSVs, freeze receipts and ledgers for a fresh start —
# e.g. before the FIRST real run (to drop the offline dry-run's MOCK artifacts,
# which otherwise trigger a MOCK/REAL mode-mismatch refusal). REAL data is only
# cleared when you explicitly ask via RESET=1.
if [ "${RESET:-0}" = "1" ]; then
  echo "   RESET=1: clearing raw CSVs, freeze receipts, ledgers for subgrid=$SUBGRID"
  for m in $MODELS; do for v in $VARIANTS; do
    for f in "data/raw/runs_${SUBGRID}_${m}_${v}.csv" "data/frozen/${SUBGRID}_${m}_${v}.freeze.json"; do
      [ -f "$f" ] && { chmod u+w "$f" 2>/dev/null || true; : > "$f"; }
    done
  done; done
  for L in manifest/ledger_${SUBGRID}_MOCK*.json manifest/ledger_${SUBGRID}_REAL*.json; do
    [ -f "$L" ] && { chmod u+w "$L" 2>/dev/null || true; : > "$L"; }
  done
fi

# MOCK is a repeatable dry-run: reset prior mock CSVs + ledgers so re-runs are clean.
# REAL is append-only and resumable: never reset real captures.
if [ "$MOCK" = "1" ]; then
  for m in $MODELS; do for v in $VARIANTS; do
    f="data/raw/runs_${SUBGRID}_${m}_${v}.csv"
    [ -f "$f" ] && { chmod u+w "$f" 2>/dev/null || true; : > "$f"; }
  done; done
  for L in manifest/ledger_${SUBGRID}_MOCK*.json; do
    [ -f "$L" ] && { chmod u+w "$L" 2>/dev/null || true; : > "$L"; }
  done
fi

# 2. capture + freeze-on-landing — PROVIDERS RUN IN PARALLEL.
# Each provider is its own background stream with its own rate limits, its own
# ledger file (_<provider>), and its own sub-cap = BUDGET/num_providers (so the
# global cap is preserved). Within a provider, models run SEQUENTIALLY — piling
# concurrent workers onto one provider is what causes 429 bursts.
MODEL_PROV=$($PY -c "import sys;sys.path.insert(0,'config');import loader as C;cfg=C.load_all();sg=C.subgrid(cfg,'$SUBGRID');print('\n'.join(f'{cfg.models.cfg(m).provider} {m}' for m in sg.models))")
PROVIDERS=$(echo "$MODEL_PROV" | awk '{print $1}' | sort -u)
NPROV=$(echo "$PROVIDERS" | wc -w | tr -d ' ')
BUDGET=$($PY -c "import sys;sys.path.insert(0,'config');import loader as C;print(getattr(C.load_all().grid.budgets,'$SUBGRID'))")
CAP_EACH=$($PY -c "print(round($BUDGET/max(1,$NPROV),4))")
echo "   parallel streams: $NPROV providers | per-provider cap \$$CAP_EACH (global \$$BUDGET) | conc/provider=$CONC"

capture_provider() {
  local prov="$1"; local models="$2"; local v m rc
  for m in $models; do
    for v in $VARIANTS; do
      # resume: a (model,variant) that is already frozen is complete — skip it so a
      # resumed run doesn't trip on the read-only frozen CSV.
      if [ "$MOCK" != "1" ] && [ -s "data/frozen/${SUBGRID}_${m}_${v}.freeze.json" ]; then
        echo "   [$prov] $m/$v already frozen — skip"; continue
      fi
      set +e
      PILOT_MOCK=$MOCK $PY capture/orchestrator.py --subgrid "$SUBGRID" --model "$m" \
        --variant "$v" --concurrency "$CONC" --ledger-suffix "_$prov" --spend-cap "$CAP_EACH"
      rc=$?
      set -e
      if [ $rc -eq 8 ]; then echo "   [$prov] $m DAILY-capped — skipping to next model (resume it after reset)"; continue 2; fi
      if [ $rc -eq 3 ]; then echo "!! [$prov] budget sub-cap stop at $m/$v (resume by re-running)"; return 3; fi
      if [ $rc -eq 6 ]; then echo "!! [$prov] preflight refusal at $m/$v"; return 6; fi
      if [ $rc -ne 0 ]; then echo "!! [$prov] capture error rc=$rc at $m/$v"; return $rc; fi
      $PY capture/freeze.py --subgrid "$SUBGRID" --model "$m" --variant "$v"
    done
  done
  echo "   [$prov] stream complete."
}

pids=(); provs=()
for prov in $PROVIDERS; do
  pm=$(echo "$MODEL_PROV" | awk -v p="$prov" '$1==p{print $2}' | tr '\n' ' ')
  echo "   stream[$prov]: $pm"
  capture_provider "$prov" "$pm" &
  pids+=($!); provs+=("$prov")
done
fail=0
for i in "${!pids[@]}"; do
  if ! wait "${pids[$i]}"; then echo "!! provider stream '${provs[$i]}' exited nonzero"; fail=1; fi
done

# spend summary across per-provider ledgers
$PY -c "import json,glob;fs=glob.glob('manifest/ledger_${SUBGRID}_${MODE}_*.json');t=sum(json.load(open(f)).get('cum_usd',0) for f in fs if __import__('os').path.getsize(f)>0);print(f'[run_all] total spend across {len(fs)} streams = \${t:.4f} / cap \$$BUDGET')"
if [ "$fail" != "0" ]; then
  echo "!! at least one stream did not finish cleanly — inspect above, re-run to resume (append-only, no re-bill)."
fi

# 3. analysis (pure, $0, frozen CSVs only). The ACTIVE paper is the pivot
#    (false-positive variance) → altrisk → pivot_claims.json. The old monoculture
#    check (analysis/run.py) is retired for the pivot and no longer run here to
#    avoid confusion (it produced a stale/mock PASS). Run it manually if ever needed.
$PY analysis/altrisk.py --subgrid "$SUBGRID" || echo "[run_all] altrisk failed — see error above"

echo "== done: pivot result -> pivot_claims.json (run: python3 analysis/altrisk.py --subgrid $SUBGRID) =="
