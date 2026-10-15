"""ONE config schema for P4 (pydantic v2). The atom is a *screening cell*:
(model_key, prompt_variant, seed_index, case_id) -> one constrained-JSON AML
screening call. This module validates models.yaml / battery.yaml / grid.yaml and
exposes typed views. Importing it does not touch the network or spend anything."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

Provider = Literal["openai", "gemini", "google", "xai", "anthropic"]

# ── canonical vocabularies (kept in sync with battery.yaml) ─────────────────
SUSPICIOUS_TYPOLOGIES = (
    "structuring", "layering", "trade_based", "mule_network",
    "shell_layering", "funnel_account", "rapid_passthrough", "cash_intensive_front",
)
DIFFICULTIES = ("easy", "medium", "hard")
DECISIONS = ("flag", "no_flag", "ERROR")   # ERROR is first-class


# ── models.yaml ─────────────────────────────────────────────────────────────
class ModelCfg(BaseModel):
    family: str
    provider: Provider
    key_env: str
    base_url: str | None = None
    api_model: str
    price_in: float = Field(ge=0)      # USD / 1M input tokens
    price_out: float = Field(ge=0)     # USD / 1M output tokens
    max_tokens: int = Field(gt=0, default=256)
    reasoning_effort: str | None = None       # e.g. "low" for reasoning-capable models (grok-4.5)
    thinking_budget: int | None = None        # Gemini: 0 disables thinking; None = model default
    pilot: bool = False
    extra: dict = Field(default_factory=dict)
    probe_receipt: dict | None = None

    @field_validator("provider")
    @classmethod
    def _norm(cls, v: str) -> str:
        return "gemini" if v == "google" else v


class ModelRegistry(BaseModel):
    models: dict[str, ModelCfg]

    def pilot_models(self) -> list[str]:
        return [k for k, m in self.models.items() if m.pilot]

    def cfg(self, key: str) -> ModelCfg:
        if key not in self.models:
            raise KeyError(f"unknown model {key!r}; have {sorted(self.models)}")
        return self.models[key]


# ── battery.yaml ────────────────────────────────────────────────────────────
class BatterySizes(BaseModel):
    full: int = Field(gt=0)
    pilot: int = Field(gt=0)

    @model_validator(mode="after")
    def _pilot_le_full(self):
        if self.pilot > self.full:
            raise ValueError("battery pilot size must be <= full size")
        return self


class BatteryCfg(BaseModel):
    seed: int
    sizes: BatterySizes
    class_balance: dict[str, float]
    difficulty_mix: dict[str, float]
    suspicious_typologies: list[str]
    benign_patterns: list[str]
    serialization: dict

    @model_validator(mode="after")
    def _check(self):
        if abs(sum(self.class_balance.values()) - 1.0) > 1e-6:
            raise ValueError("class_balance must sum to 1")
        if abs(sum(self.difficulty_mix.values()) - 1.0) > 1e-6:
            raise ValueError("difficulty_mix must sum to 1")
        if set(self.suspicious_typologies) - set(SUSPICIOUS_TYPOLOGIES):
            raise ValueError("battery typology not in canonical SUSPICIOUS_TYPOLOGIES")
        return self


# ── grid.yaml ───────────────────────────────────────────────────────────────
class Budgets(BaseModel):
    pilot: float = Field(gt=0)
    full: float = Field(gt=0)


class Subgrid(BaseModel):
    models: list[str]
    variants: list[str]
    seed_indices: list[int]
    battery: Literal["pilot", "full"]


class GridCfg(BaseModel):
    seed_master: int
    analysis_seed: int
    budgets: Budgets
    stop_margin_usd: float = 0.05
    max_workers: int = Field(gt=0, default=5)
    max_retries: int = Field(ge=0, default=10)
    judge_temperature: float = 0.0
    rpm_limits: dict[str, float] = Field(default_factory=dict)
    daily_limits: dict[str, int] = Field(default_factory=dict)
    prompt_variants: list[str]
    subgrids: dict[str, Subgrid]
    pilot_requires_cheap: bool = True


# ── the run-time atom ───────────────────────────────────────────────────────
class ScreeningCell(BaseModel):
    """One unit of capture. Fully identifies a single billable screening call."""
    model_key: str
    prompt_variant: str
    seed_index: int
    case_id: str

    def key(self) -> tuple[str, str, int, str]:
        return (self.model_key, self.prompt_variant, self.seed_index, self.case_id)
