# PILOT_RESULTS — P4  (mode=REAL)

Config hash `44d182dea86c0285` · battery(pilot) `48ee5fead84358fd...` · seed 4242 · draws 2000.
3840 rows, 0 ERROR (0.000), spend $0.8871.
Suspicious cases: 120 · common support: 120.

## Headline estimands
| Estimand | Point | 95% CI |
|---|---|---|
| Joint-miss ratio R (primary) | n/a | [n/a] |
| J_observed | 0.0000 | [0.0000, 0.0000] |
| J_independence | 0.0000 | — |
| Systemic-failure ratio (Bommasani) | n/a | — |
| Heterogeneous 2nd-line recovery | n/a | [n/a] |
| Homogeneous 2nd-line recovery | n/a | — |
| Within−cross family κ contrast | n/a | [n/a] |
| Pooled per-model miss rate | 0.000 | — |

## Per-model marginal miss rate
| model | family | miss rate | n | Wilson CI |
|---|---|---|---|---|
| gemini_flash | google | 0.000 | 120 | [-0.00, 0.03] |
| gemini_flash_lite | google | 0.000 | 120 | [-0.00, 0.03] |
| openai_41_mini | openai | 0.000 | 120 | [-0.00, 0.03] |
| openai_4o_mini | openai | 0.000 | 120 | [-0.00, 0.03] |

## Pairwise Cohen κ on misses
| pair | κ |
|---|---|
| gemini_flash_lite|openai_41_mini | n/a |
| gemini_flash_lite|openai_4o_mini | n/a |
| gemini_flash|gemini_flash_lite | n/a |
| gemini_flash|openai_41_mini | n/a |
| gemini_flash|openai_4o_mini | n/a |
| openai_41_mini|openai_4o_mini | n/a |

## Robustness
Prevalence/churn: {'marginal_miss_spread': 0.0, 'mean_churn_component': 0.0, 'mean_disagreement': 0.0, 'mean_prevalence_component': 0.0}.
Chance-corrected agreement is reported under three statistics (κ, Scott π, Gwet AC1)
in claims.json; a finding that flipped sign across them would be flagged non-robust.

> REAL capture.
