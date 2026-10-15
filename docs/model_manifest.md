# Model manifest (served snapshots)

Exact model strings served during capture, recorded per row (`api_model`).

| model_key | provider | family | served api_model |
|---|---|---|---|
| gemini_flash | gemini | google | `gemini-flash-latest` |
| gemini_flash_lite | gemini | google | `gemini-flash-lite-latest` |
| openai_41_mini | openai | openai | `gpt-4.1-mini-2025-04-14` |
| openai_4o | openai | openai | `gpt-4o-2024-11-20` |
| openai_4o_mini | openai | openai | `gpt-4o-mini-2024-07-18` |

Notes:
- Gemini models use `-latest` aliases resolving to the current stable release at capture time (Gemini 3.5 Flash / 2.5 Flash-Lite); the 2.0 Flash snapshots were deprecated 2026-06-01.
- Temperature 0; constrained-JSON output. See `docs/data_collection.md`.
- xAI Grok and Gemini Pro appear in `data/configs/` but were excluded from the final grid (xAI out of credits; Gemini Pro is a forced-thinking model unsuited to high-volume screening) — see `docs/decisions_log.md` D17/D19.
