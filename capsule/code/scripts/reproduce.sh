#!/usr/bin/env bash
# Offline, deterministic reproduction of "AI foundation model choice and false positive variation in Anti Money Laundering transaction screening".
# Verifies data integrity, runs the analysis, and (by default) the byte-identical
# reproducibility check. No network, no API keys, no cost.
#
#   bash code/scripts/reproduce.sh                # verify + analyze + replication check
#   bash code/scripts/reproduce.sh --analyze-only # verify + analyze only
#   bash code/scripts/reproduce.sh --check-only   # replication check only
set -euo pipefail

# Path layout: Code Ocean mounts /code /data /results; local uses the capsule root.
if [[ -d /code/src && -d /data ]]; then
  CODE=/code; DATA=/data; RESULTS=/results
else
  ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
  CODE="$ROOT/code"; DATA="$ROOT/data"; RESULTS="$ROOT/results"
fi
export PYTHONPATH="$CODE/src:${PYTHONPATH:-}"
export POD_DATA_DIR="$DATA"
export POD_RESULTS_DIR="$RESULTS"
mkdir -p "$RESULTS"

PYBIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYBIN" ]]; then echo "ERROR: python not found on PATH." >&2; exit 1; fi
if ! "$PYBIN" -c "import numpy, sklearn, yaml, pydantic" 2>/dev/null; then
  echo "ERROR: missing packages. Install: pip install -r code/requirements.txt" >&2; exit 1
fi

MODE="${1:-all}"
echo "== Reproducing: AI foundation model choice and false positive variation in Anti Money Laundering transaction screening =="
echo "   data=$DATA"
echo "   results=$RESULTS"
echo "   python=$("$PYBIN" --version 2>&1)"

if [[ "$MODE" != "--check-only" ]]; then
  "$PYBIN" "$CODE/src/reproduce.py"
fi
if [[ "$MODE" != "--analyze-only" ]]; then
  "$PYBIN" "$CODE/src/replication_check.py"
fi
echo "== Done. Open results/metrics_summary.md, results/replication_check.md,"
echo "   results/table1_operating_points.md, results/table2_alert_volume.md =="
