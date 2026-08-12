#!/usr/bin/env bash
# Top-level convenience entry point. Delegates to code/scripts/reproduce.sh.
#   bash reproduce.sh                 # verify + analyze + reproducibility check
#   bash reproduce.sh --analyze-only
#   bash reproduce.sh --check-only
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec bash "$ROOT/code/scripts/reproduce.sh" "$@"
