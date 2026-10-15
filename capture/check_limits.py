"""Show your LIVE OpenAI (and Gemini) rate limits by reading the rate-limit headers
returned on a 1-token call. The per-minute request limit reveals your tier:

  gpt-4o-mini  x-ratelimit-limit-requests = 500  -> Tier 1
                                           = 5000 -> Tier 2  (etc.)

The daily (RPD/TPD) cap is NOT in the headers — it only appears in a 429 body — but
the per-minute limit tells you whether a tier upgrade has actually taken effect.

  python capture/check_limits.py
Run locally where the keys + network work.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secrets as secretstore  # noqa: E402

_RL_KEYS = ["x-ratelimit-limit-requests", "x-ratelimit-remaining-requests",
            "x-ratelimit-reset-requests", "x-ratelimit-limit-tokens",
            "x-ratelimit-remaining-tokens", "x-ratelimit-reset-tokens"]
_TIER_HINT = {"500": "Tier 1", "5000": "Tier 2", "10000": "Tier 3",
              "30000": "Tier 4"}


def check_openai(models=("gpt-4o-mini", "gpt-4.1-mini", "gpt-4o")):
    from openai import OpenAI
    pool = secretstore.get_pool("openai")
    if not pool:
        print("no OpenAI key found"); return
    print(f"OpenAI: {len(pool)} key(s) in pool. Probing rate-limit headers per model:\n")
    # all keys usually share one org -> one limit; probe with the first key
    client = OpenAI(api_key=pool[0], max_retries=0)
    for model in models:
        try:
            resp = client.chat.completions.with_raw_response.create(
                model=model, max_tokens=1,
                messages=[{"role": "user", "content": "ping"}])
            h = resp.headers
            rpm = h.get("x-ratelimit-limit-requests")
            tier = _TIER_HINT.get(str(rpm), "?")
            print(f"  {model}")
            print(f"    RPM limit (x-ratelimit-limit-requests) = {rpm}  -> {tier}")
            for k in _RL_KEYS[1:]:
                print(f"    {k} = {h.get(k)}")
            print()
        except Exception as e:
            msg = str(e)
            print(f"  {model}: ERROR {msg[:220]}")
            if "per day" in msg.lower() or "rpd" in msg.lower():
                print("    -> this model's DAILY request cap is exhausted for today "
                      "(resets ~midnight UTC).")
            print()


def check_gemini():
    try:
        pool = secretstore.get_pool("gemini")
    except Exception:
        pool = []
    print(f"Gemini: {len(pool)} key(s) in pool. (Google does not return per-minute "
          f"limit headers; watch for 429 RESOURCE_EXHAUSTED instead.)")


if __name__ == "__main__":
    check_openai()
    check_gemini()
