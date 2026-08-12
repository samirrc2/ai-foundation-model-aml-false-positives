"""Sanity checks on the reproduced results. Run with: pytest code/tests -q
(from the capsule root, with code/src on PYTHONPATH). These assert the headline
numbers in the paper and that data integrity + byte-identical re-run hold."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import io_paths  # noqa: E402


def _run(results_dir):
    env = dict(os.environ)
    env["POD_RESULTS_DIR"] = str(results_dir)
    env["POD_DATA_DIR"] = str(io_paths.DATA_DIR)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, str(SRC / "reproduce.py")], check=True, env=env,
                   capture_output=True)
    return results_dir


def test_data_integrity_and_headlines():
    with tempfile.TemporaryDirectory() as d:
        out = _run(Path(d))
        integ = json.loads((out / "data_integrity.json").read_text())
        assert integ["all_ok"], "data integrity failed"

        claims = json.loads((out / "pivot_claims.json").read_text())
        A = claims["A_false_positive"]
        # 82.7pp spread, ~249x ratio, 85.7% divergence
        assert abs(A["fp_spread_pp"] - 0.827) < 0.01
        assert A["divergence_benign"] > 0.80
        fp = {m: d["fp_rate"] for m, d in A["per_model"].items()}
        assert fp["gemini_flash"] < 0.02 and fp["openai_4o_mini"] > 0.78
        # trade-based blind spot + prompt flip
        assert claims["B_typology_miss"]["trade_based"]["miss_rate"] > 0.10
        assert claims["C_prompt_flip"]["flip_rate"] < 0.12

        base = json.loads((out / "baselines.json").read_text())
        assert abs(base["rules"]["fp"] - 0.12) < 0.02
        assert base["supervised"]["grad_boost"]["fp"] < 0.02


def test_byte_identical_rerun():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        h1 = json.loads((_run(Path(a)) / "output_hashes.json").read_text())
        h2 = json.loads((_run(Path(b)) / "output_hashes.json").read_text())
        assert h1 == h2, "outputs are not byte-identical across runs"
