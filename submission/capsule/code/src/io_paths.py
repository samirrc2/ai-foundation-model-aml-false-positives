"""Path resolution for the Code Ocean capsule. Works in two layouts:

  * Code Ocean run:   /data (read-only), /results (writable), /code
  * Local checkout:   <capsule>/data, <capsule>/results, <capsule>/code

All modules import DATA/RESULTS/… from here so nothing hard-codes a location.
"""
from __future__ import annotations
import os
from pathlib import Path


def _detect():
    env_data = os.environ.get("POD_DATA_DIR")
    env_results = os.environ.get("POD_RESULTS_DIR")
    if env_data and env_results:
        return Path(env_data), Path(env_results)
    if Path("/data").is_dir() and Path("/code").is_dir():
        return Path("/data"), Path("/results")
    root = Path(__file__).resolve().parents[2]      # code/src/io_paths.py -> capsule/
    return root / "data", root / "results"


DATA_DIR, RESULTS_DIR = _detect()
BATTERY_DIR = DATA_DIR / "battery"
CAPTURE_DIR = DATA_DIR / "capture"
FROZEN_DIR = DATA_DIR / "frozen"
CONFIG_DIR = DATA_DIR / "configs"
MANIFEST_DIR = DATA_DIR / "manifest"


def ensure_results() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR
