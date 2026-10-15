"""Config loader for P4. Parses + validates the three YAMLs into typed views and
resolves a subgrid into the list of screening cells to capture. Enforces the
pilot-cheap-only guard so a flagship can never enter a <=$10 pilot."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import ModelRegistry, BatteryCfg, GridCfg, ScreeningCell  # noqa: E402
import io_paths  # noqa: E402

_HERE = Path(__file__).resolve().parent


def _load_yaml(name: str) -> dict:
    return yaml.safe_load((io_paths.CONFIG_DIR / name).read_text())


@dataclass(frozen=True)
class Config:
    models: ModelRegistry
    battery: BatteryCfg
    grid: GridCfg
    raw: dict            # the three raw dicts, for hashing

    def config_hash(self) -> str:
        blob = json.dumps(self.raw, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:16]


def load_all() -> Config:
    m = _load_yaml("models.yaml")
    b = _load_yaml("battery.yaml")
    g = _load_yaml("grid.yaml")
    cfg = Config(
        models=ModelRegistry.model_validate(m),
        battery=BatteryCfg.model_validate(b),
        grid=GridCfg.model_validate(g),
        raw={"models": m, "battery": b, "grid": g},
    )
    _validate_subgrids(cfg)
    return cfg


def _validate_subgrids(cfg: Config) -> None:
    for name, sg in cfg.grid.subgrids.items():
        for mk in sg.models:
            mc = cfg.models.cfg(mk)   # raises on unknown
            if name == "pilot" and cfg.grid.pilot_requires_cheap and not mc.pilot:
                raise ValueError(
                    f"PILOT GUARD: subgrid 'pilot' references non-pilot (flagship) "
                    f"model {mk!r}. Flagships are reserved for the full run.")
        for v in sg.variants:
            if v not in cfg.grid.prompt_variants:
                raise ValueError(f"subgrid {name!r} uses unknown variant {v!r}")


def subgrid(cfg: Config, name: str):
    if name not in cfg.grid.subgrids:
        raise KeyError(f"unknown subgrid {name!r}; have {sorted(cfg.grid.subgrids)}")
    return cfg.grid.subgrids[name]


def cells_for(cfg: Config, subgrid_name: str, case_ids: list[str],
              model_key: str | None = None, variant: str | None = None) -> list[ScreeningCell]:
    """Enumerate screening cells for a subgrid. If model_key/variant given, restrict
    to that model / that prompt variant (orchestrator captures one CSV per
    (model, variant))."""
    sg = subgrid(cfg, subgrid_name)
    models = [model_key] if model_key else sg.models
    variants = [variant] if variant else sg.variants
    out: list[ScreeningCell] = []
    for mk in models:
        for v in variants:
            for si in sg.seed_indices:
                for cid in case_ids:
                    out.append(ScreeningCell(model_key=mk, prompt_variant=v,
                                             seed_index=si, case_id=cid))
    return out


if __name__ == "__main__":
    c = load_all()
    print("config_hash:", c.config_hash())
    print("models     :", list(c.models.models))
    print("pilot set  :", c.models.pilot_models())
    for name, sg in c.grid.subgrids.items():
        print(f"  subgrid {name:5s}: {len(sg.models)} models x {len(sg.variants)} "
              f"variants x {len(sg.seed_indices)} seeds | battery={sg.battery}")
    print("budgets    :", c.grid.budgets.pilot, "/", c.grid.budgets.full)
