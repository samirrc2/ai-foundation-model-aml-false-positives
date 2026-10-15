"""Path resolution for the archive. One layout, one root.

The repository is flat: analysis/, data/, results/ all sit beside each other. The Code Ocean
mount detection that used to live here (/code, /data, /results) is gone with the move to
Zenodo. POD_DATA_DIR and POD_RESULTS_DIR are still honoured so the test suite can redirect
outputs to a temporary directory.

All modules import DATA/RESULTS from here so nothing hard-codes a location.
"""
from __future__ import annotations
import os
from pathlib import Path


def _detect():
    env_data = os.environ.get("POD_DATA_DIR")
    env_results = os.environ.get("POD_RESULTS_DIR")
    if env_data and env_results:
        return Path(env_data), Path(env_results)
    root = Path(__file__).resolve().parents[1]      # analysis/io_paths.py -> repo root
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
