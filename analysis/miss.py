"""Per-cell miss (false-negative) determination — the pure foundation of analysis.

Reads FROZEN capture CSVs only (each runs_<model>_<variant>.csv must have a
matching data/frozen/<...>.freeze.json whose SHA-256 matches; --allow-unfrozen
relaxes this for the analyst dev loop). Reduces replicate decisions to a per
(model, case) MODAL miss indicator over suspicious cases (ties -> flag, the
conservative resolution). ERROR is first-class: excluded from the vote; an
all-ERROR (model, case) is NA and dropped from that model's support.
"""
from __future__ import annotations
import csv, hashlib, json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_RAW = _HERE.parent / "data" / "raw"
_FROZEN = _HERE.parent / "data" / "frozen"


@dataclass
class MissTable:
    models: list[str]                                   # sorted model keys present
    family: dict[str, str]                              # model -> family
    cases_meta: dict[str, dict]                         # case_id -> {label,typology,stratum,difficulty}
    miss: dict[str, dict[str, int | None]]              # model -> case_id -> 0/1/None (suspicious only)
    flag_benign: dict[str, dict[str, int | None]]       # model -> case_id -> 0/1/None (benign only)
    n_rows: int = 0
    n_error: int = 0
    variants: set = field(default_factory=set)
    seed_indices: set = field(default_factory=set)
    mode: str = ""

    # ── views ────────────────────────────────────────────────────────────────
    def suspicious_cases(self) -> list[str]:
        return sorted(c for c, m in self.cases_meta.items() if m["label"] == "suspicious")

    def benign_cases(self) -> list[str]:
        return sorted(c for c, m in self.cases_meta.items() if m["label"] == "benign")

    def common_support(self, models: list[str] | None = None) -> list[str]:
        """Suspicious cases where every listed model has a non-NA miss indicator."""
        models = models or self.models
        out = []
        for c in self.suspicious_cases():
            if all(self.miss.get(m, {}).get(c) is not None for m in models):
                out.append(c)
        return out

    def stratum_of(self, case_id: str) -> str:
        return self.cases_meta[case_id]["stratum"]

    def cases_by_stratum(self, case_ids: list[str]) -> dict[str, list[str]]:
        out = defaultdict(list)
        for c in case_ids:
            out[self.stratum_of(c)].append(c)
        return dict(out)


def _frozen_ok(csv_path: Path) -> tuple[bool, str]:
    receipt = _FROZEN / f"{csv_path.stem.replace('runs_', '', 1)}.freeze.json"
    if not receipt.exists() or receipt.stat().st_size == 0:
        return False, "no/empty freeze receipt"
    try:
        r = json.loads(receipt.read_text())
    except (ValueError, OSError):
        return False, "corrupt freeze receipt"
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if digest != r.get("sha256"):
        return False, "sha256 mismatch (CSV changed after freeze)"
    return True, "ok"


def _modal(decisions: list[str], want: str) -> int | None:
    """Modal indicator over non-ERROR decisions: 1 if majority == `want`, else 0;
    ties break AGAINST `want` (conservative for misses); None if all ERROR."""
    valid = [d for d in decisions if d in ("flag", "no_flag")]
    if not valid:
        return None
    k = sum(1 for d in valid if d == want)
    return 1 if k > len(valid) / 2 else 0


def _csv_model(path: Path) -> str | None:
    with path.open() as f:
        r = next(csv.DictReader(f), None)
    return r["model_key"] if r else None


def load_miss_table(subgrid_filter: str | None = None, allow_unfrozen: bool = False,
                    raw_dir: Path | None = None,
                    allowed_models: set[str] | None = None) -> MissTable:
    raw_dir = raw_dir or _RAW
    glob = f"runs_{subgrid_filter}_*.csv" if subgrid_filter else "runs_*.csv"
    csvs = sorted(p for p in raw_dir.glob(glob) if p.stat().st_size > 0)
    # Restrict to the subgrid's DECLARED models so stray CSVs (e.g. leftover MOCK
    # files, or a model dropped from the subgrid) never contaminate the analysis.
    if allowed_models is not None:
        csvs = [p for p in csvs if _csv_model(p) in allowed_models]
    if not csvs:
        raise FileNotFoundError(f"no {glob} in {raw_dir} — capture first")

    raw_dec: dict[tuple[str, str], list[str]] = defaultdict(list)   # (model,case)->decisions
    cases_meta: dict[str, dict] = {}
    family: dict[str, str] = {}
    n_rows = n_error = 0
    variants, seeds, modes = set(), set(), set()

    for path in csvs:
        ok, why = _frozen_ok(path)
        if not ok and not allow_unfrozen:
            raise RuntimeError(
                f"ANALYSIS WALL: {path.name} is not frozen ({why}). Run "
                f"capture/freeze.py, or pass --allow-unfrozen for the dev loop.")
        for r in csv.DictReader(path.open()):
            if subgrid_filter and r.get("subgrid") != subgrid_filter:
                continue
            n_rows += 1
            modes.add(r.get("mode", ""))
            variants.add(r["prompt_variant"]); seeds.add(int(r["seed_index"]))
            family[r["model_key"]] = r["family"]
            cid = r["case_id"]
            cases_meta.setdefault(cid, {
                "label": r["label"], "typology": r.get("typology") or None,
                "stratum": r["stratum"], "difficulty": r["difficulty"]})
            dec = r["decision"]
            if dec == "ERROR":
                n_error += 1
            raw_dec[(r["model_key"], cid)].append(dec)

    models = sorted(family)
    miss: dict[str, dict[str, int | None]] = {m: {} for m in models}
    flag_benign: dict[str, dict[str, int | None]] = {m: {} for m in models}
    for (m, cid), decs in raw_dec.items():
        label = cases_meta[cid]["label"]
        if label == "suspicious":
            miss[m][cid] = _modal(decs, "no_flag")
        else:
            flag_benign[m][cid] = _modal(decs, "flag")

    return MissTable(models=models, family=family, cases_meta=cases_meta, miss=miss,
                     flag_benign=flag_benign, n_rows=n_rows, n_error=n_error,
                     variants=variants, seed_indices=seeds,
                     mode=("MOCK" if modes == {"MOCK"} else
                           ("REAL" if modes == {"REAL"} else "MIXED")))


def error_rate(mt: MissTable) -> float:
    return mt.n_error / max(1, mt.n_rows)
