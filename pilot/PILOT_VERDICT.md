# PILOT_VERDICT — P4

**Subgrid:** `full`  ·  **Mode:** `MOCK`  ·  **Config hash:** `5b3fa611813d27f7`
**Models:** gemini_flash, gemini_flash_lite, openai_41_mini, openai_4o, openai_4o_mini, xai_grok
**Battery:** pilot sha256 `518115ac0e0690bf...`  ·  **Analysis seed:** 4242  ·  **Bootstrap draws:** 2000

> Pre-registered pilot gate (PREREGISTRATION §5). All three must hold to clear the
> full run. This file only reports; it never starts the full run.

## Criterion 1 — Ran clean  🟢 GREEN
End-to-end, resumable, **0 ERROR** records (0.000 rate),
total spend **$0.0000** ≤ cap **$25.00**.
Rows captured: 14400.

## Criterion 2 — Measurable base rate  🟢 GREEN
Pooled per-model miss (false-negative) rate = **0.283**,
target band **[0.10, 0.70]**. Inside band — variance exists to correlate.


## Criterion 3 — Estimable correlation with signal  🟢 GREEN
Cross-model joint-miss ratio (observed / independence) = **295.20**,
95% CI **[151.34, 717.70]** (excludes 1: **True**).
J_observed = 0.1133 vs J_independence = 0.0004.
Within-family vs cross-family κ contrast = **0.149**
(within 0.726 − cross 0.577),
CI [0.12, 0.18] — contrast computable: **True**.

---

## PILOT: PASS → cleared for full run
