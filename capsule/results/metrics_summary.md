# Metrics summary — AI foundation model choice and false positive variation in Anti Money Laundering transaction screening

Models: gemini_flash, gemini_flash_lite, openai_41_mini, openai_4o, openai_4o_mini
Battery: 300 benign / 300 suspicious | error rate 0.0008

## Headline (false-positive variance)
- FP spread (max−min): **82.7 pp** ([69.2–95.3])
- FP ratio (max/min): ~249× (secondary; min is a single event)
- Cross-model disagreement on benign: **85.7%** ([75.1–95.4])

## Per-model false-positive rate
- gemini_flash: 0.3% [0.1–1.9] (1/300)
- openai_4o: 1.0% [0.3–2.9] (3/300)
- openai_41_mini: 23.7% [19.2–28.8] (71/300)
- gemini_flash_lite: 24.7% [20.1–29.8] (74/300)
- openai_4o_mini: 83.0% [78.3–86.8] (249/300)

## Baselines (same battery)
- Rules (FATF heuristics): FP 12.0% / miss 11.3%
- Supervised (gradient boosting, out-of-fold): FP 0.0% / miss 0.0%

## Operational projection (1,000,000 tx/day @ 0.1% prevalence)
- Daily alert volume across models: 4,210 → 830,170 (~197× on the identical book)

## Supporting
- Trade-based blind spot (pooled miss): 18.9%
- Prompt-variant flip: 7.5%
