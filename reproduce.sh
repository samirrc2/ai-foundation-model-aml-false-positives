#!/usr/bin/env bash
# Offline, deterministic reproduction of "AI foundation model choice and false positive variation in Anti Money Laundering transaction screening".
# Verifies data integrity, runs the analysis, and (by default) the byte-identical
# reproducibility check. No network, no API keys, no cost.
#
#   bash reproduce.sh                # verify + analyze + replication check
#   bash reproduce.sh --analyze-only # verify + analyze only
#   bash reproduce.sh --check-only   # replication check only
set -euo pipefail

# One flat layout. The Code Ocean /code /data /results mount detection is gone with the move
# to Zenodo: the archive is a plain source release, so the repository root is the only root.
ROOT="$(cd "$(dirname "$0")" && pwd)"
CODE="$ROOT/analysis"; DATA="$ROOT/data"; RESULTS="$ROOT/results"
export PYTHONPATH="$CODE:${PYTHONPATH:-}"
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
  "$PYBIN" "$CODE/reproduce.py"
fi
if [[ "$MODE" != "--analyze-only" ]]; then
  "$PYBIN" "$CODE/replication_check.py"
fi
echo "== Done. Open results/metrics_summary.md, results/replication_check.md,"
echo "   results/table1_operating_points.md, results/table2_alert_volume.md =="
