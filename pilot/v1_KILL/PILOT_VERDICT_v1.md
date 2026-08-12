# PILOT_VERDICT — P4

**Subgrid:** `pilot`  ·  **Mode:** `REAL`  ·  **Config hash:** `44d182dea86c0285`
**Models:** gemini_flash, gemini_flash_lite, openai_41_mini, openai_4o_mini
**Battery:** pilot sha256 `48ee5fead84358fd...`  ·  **Analysis seed:** 4242  ·  **Bootstrap draws:** 2000

> Pre-registered pilot gate (PREREGISTRATION §5). All three must hold to clear the
> full run. This file only reports; it never starts the full run.

## Criterion 1 — Ran clean  🟢 GREEN
End-to-end, resumable, **0 ERROR** records (0.000 rate),
total spend **$0.8871** ≤ cap **$10.00**.
Rows captured: 3840.

## Criterion 2 — Measurable base rate  🔴 RED
Pooled per-model miss (false-negative) rate = **0.000**,
target band **[0.10, 0.70]**. OUT OF BAND — nothing to correlate → KILL.

## Criterion 3 — Estimable correlation with signal  🔴 RED
Cross-model joint-miss ratio (observed / independence) = **n/a**,
95% CI **[n/a]** (excludes 1: **None**).
J_observed = 0.0000 vs J_independence = 0.0000.
Within-family vs cross-family κ contrast = **n/a**
(within n/a − cross n/a),
CI [n/a] — contrast computable: **False**.

---

## PILOT: KILL (criterion 2 — pooled miss rate 0.000 out of the 0.10-0.70 measurable band; no variance to correlate)
