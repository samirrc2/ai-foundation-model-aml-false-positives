"""Sanity checks on the reproduced results. Run with: pytest tests -q from the repository
root. These assert the headline numbers in the paper and that data integrity and the
byte-identical re-run hold."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "analysis"
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
        # Primary rule = preregistered D4 (ties -> flag, label-independent):
        # 83.3 pp spread, 88.7% divergence, FP 2.3% .. 85.7%.
        # The submitted analysis deviated from D4 on the legitimate-case branch and
        # reported 82.7 pp with FP 0.3% .. 83.0%; those values must NOT return.
        assert abs(A["fp_spread_pp"] - 0.8333) < 0.005
        assert A["divergence_benign"] > 0.85
        fp = {m: d["fp_rate"] for m, d in A["per_model"].items()}
        assert 0.020 < fp["gemini_flash"] < 0.026, "gemini_flash FP left the D4 value"
        assert 0.85 < fp["openai_4o_mini"] < 0.87, "openai_4o_mini FP left the D4 value"
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


def test_aggregation_rule_is_label_independent():
    """The tie direction must be fixed, not chosen from the ground-truth label."""
    import aggregate as AGG          # SRC is already on sys.path (module header)
    tie = ["flag", "flag", "no_flag", "no_flag"]
    assert AGG.modal_decision(tie) == "flag"
    # one fixed direction: a tie is a false positive on a benign case AND not a miss
    assert AGG.modal_indicator(tie, "flag") == 1
    assert AGG.modal_indicator(tie, "no_flag") == 0
    assert AGG.modal_decision(["ERROR", "ERROR"]) is None
    assert AGG.modal_decision(["ERROR", "flag", "no_flag"]) == "flag"


def test_small_p_values_survive_serialisation():
    """stats_tests.json rounded to 4 d.p. and recorded every p below 5e-5 as 0.0."""
    with tempfile.TemporaryDirectory() as d:
        out = _run(Path(d))
        st = json.loads((out / "stats_tests.json").read_text())
        assert st["cochran_q"]["p"] > 0.0, "Cochran p serialised as exactly 0.0"
        assert st["cochran_q"]["p"] < 1e-20
        zeros = [k for k, v in st["pairwise_mcnemar"].items()
                 if v["p_bonferroni"] == 0.0]
        assert not zeros, f"pairwise p serialised as exactly 0.0: {zeros}"


def test_aggregation_sensitivity_emitted():
    with tempfile.TemporaryDirectory() as d:
        out = _run(Path(d))
        a = json.loads((out / "aggregation_sensitivity.json").read_text())
        assert a["policies"]["ties_to_flag_preregistered_D4"]["primary"] is True
        lo, hi = a["fp_spread_range_pp"]
        assert 70 < lo and hi < 90, "spread left the range reported in the revision"
        assert a["calls"]["realized"] == 12120 and a["calls"]["designed"] == 12000
