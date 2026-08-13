"""Reproducibility audit: run the full analysis TWICE into separate output folders
and confirm the outputs are byte-identical (SHA-256), and that data-integrity
verification passes. Writes results/replication_check.md with PASS/FAIL.

  python code/src/replication_check.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import io_paths  # noqa: E402

_SRC = Path(__file__).resolve().parent


def _run_into(results_dir: Path) -> dict:
    env = dict(os.environ)
    env["POD_RESULTS_DIR"] = str(results_dir)
    env["POD_DATA_DIR"] = str(io_paths.DATA_DIR)
    env["PYTHONPATH"] = str(_SRC) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, str(_SRC / "reproduce.py")],
                   check=True, env=env, capture_output=True)
    return json.loads((results_dir / "output_hashes.json").read_text())


def main() -> int:
    out = io_paths.ensure_results()
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        h1 = _run_into(Path(a))
        h2 = _run_into(Path(b))
        integ = json.loads((Path(a) / "data_integrity.json").read_text())

    identical = h1 == h2
    keys = sorted(set(h1) | set(h2))
    lines = ["# Reproducibility check", "",
             f"**Data integrity:** {'PASS' if integ['all_ok'] else 'FAIL'} "
             f"(battery + capture SHA-256 match manifest/receipts)",
             f"**Byte-identical re-run:** {'PASS' if identical else 'FAIL'}", "",
             "| Output | SHA-256 (run 1) | identical? |", "|---|---|---|"]
    for k in keys:
        same = h1.get(k) == h2.get(k)
        lines.append(f"| {k} | `{(h1.get(k) or '')[:16]}…` | {'✓' if same else '✗ DIFFERS'} |")
    verdict = "REPRODUCIBLE" if (identical and integ["all_ok"]) else "NOT REPRODUCIBLE"
    lines += ["", f"## {verdict}"]
    (out / "replication_check.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if (identical and integ["all_ok"]) else 1


if __name__ == "__main__":
    sys.exit(main())
