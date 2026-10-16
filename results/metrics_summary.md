# Metrics summary — AI foundation model choice and false positive variation in Anti Money Laundering (AML) transaction screening

Models: gemini_flash, gemini_flash_lite, openai_41_mini, openai_4o, openai_4o_mini
Battery: 300 benign / 300 suspicious | error rate 0.0008

## Headline (false-positive variance)
- FP spread (max−min): **83.3 pp** ([71.8–93.7])
- FP ratio (max/min): ~37× (secondary; min is a single event)
- Cross-model disagreement on benign: **88.7%** ([82.2–95.0])

## Per-model false-positive rate
- gemini_flash: 2.3% [1.1–4.7] (7/300)
- openai_4o: 7.7% [5.2–11.2] (23/300)
- openai_41_mini: 37.0% [31.7–42.6] (111/300)
- gemini_flash_lite: 44.0% [38.5–49.7] (132/300)
- openai_4o_mini: 85.7% [81.2–89.2] (257/300)

## Baselines (same battery)
- Rules (FATF heuristics): FP 12.0% / miss 11.3%
- Supervised (gradient boosting, out-of-fold): FP 0.0% / miss 0.0%

## Operational projection (1,000,000 tx/day @ 0.1% prevalence)
- Daily alert volume across models: 24,190 → 856,810 (~35× on the identical book)

## Supporting
- Trade-based blind spot (pooled miss): 18.9%
- Prompt-variant flip: 7.5%
