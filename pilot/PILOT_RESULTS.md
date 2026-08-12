# PILOT_RESULTS — P4  (mode=MOCK)

Config hash `5b3fa611813d27f7` · battery(pilot) `518115ac0e0690bf...` · seed 4242 · draws 2000.
14400 rows, 0 ERROR (0.000), spend $0.0000.
Suspicious cases: 300 · common support: 300.

## Headline estimands
| Estimand | Point | 95% CI |
|---|---|---|
| Joint-miss ratio R (primary) | 295.20 | [151.34, 717.70] |
| J_observed | 0.1133 | [0.0839, 0.1429] |
| J_independence | 0.0004 | — |
| Systemic-failure ratio (Bommasani) | 295.20 | — |
| Heterogeneous 2nd-line recovery | 0.354 | [0.29, 0.42] |
| Homogeneous 2nd-line recovery | 0.214 | — |
| Within−cross family κ contrast | 0.149 | [0.12, 0.18] |
| Pooled per-model miss rate | 0.283 | — |

## Per-model marginal miss rate
| model | family | miss rate | n | Wilson CI |
|---|---|---|---|---|
| gemini_flash | google | 0.283 | 300 | [0.24, 0.34] |
| gemini_flash_lite | google | 0.170 | 300 | [0.13, 0.22] |
| openai_41_mini | openai | 0.307 | 300 | [0.26, 0.36] |
| openai_4o | openai | 0.453 | 300 | [0.40, 0.51] |
| openai_4o_mini | openai | 0.287 | 300 | [0.24, 0.34] |
| xai_grok | xai | 0.200 | 300 | [0.16, 0.25] |

## Pairwise Cohen κ on misses
| pair | κ |
|---|---|
| gemini_flash_lite|openai_41_mini | 0.490 |
| gemini_flash_lite|openai_4o | 0.396 |
| gemini_flash_lite|openai_4o_mini | 0.508 |
| gemini_flash_lite|xai_grok | 0.658 |
| gemini_flash|gemini_flash_lite | 0.683 |
| gemini_flash|openai_41_mini | 0.720 |
| gemini_flash|openai_4o | 0.590 |
| gemini_flash|openai_4o_mini | 0.681 |
| gemini_flash|xai_grok | 0.649 |
| openai_41_mini|openai_4o | 0.696 |
| openai_41_mini|openai_4o_mini | 0.872 |
| openai_41_mini|xai_grok | 0.583 |
| openai_4o_mini|xai_grok | 0.624 |
| openai_4o|openai_4o_mini | 0.653 |
| openai_4o|xai_grok | 0.449 |

## Robustness
Prevalence/churn: {'marginal_miss_spread': 0.2833333333333333, 'mean_churn_component': 0.04177777777777779, 'mean_disagreement': 0.15777777777777777, 'mean_prevalence_component': 0.11600000000000002}.
Chance-corrected agreement is reported under three statistics (κ, Scott π, Gwet AC1)
in claims.json; a finding that flipped sign across them would be flagged non-robust.

> MOCK data — pipeline validation only, NOT a scientific result (DECISIONS D9).
