"""The AML screener call. Builds a supervisory constrained-JSON screening prompt
(one of the pre-registered variants), calls one model version through an
OpenAI-compatible / Gemini router with a round-robin key pool + failover, and
parses a STRICT verdict -> flag | no_flag | ERROR (ERROR is first-class).

PILOT_MOCK=1 swaps a deterministic fake screener that (a) yields a measurable
miss base-rate and (b) makes misses CORRELATED across models (shared per-case
latent hardness, plus an extra family-shared component), so the whole
capture->analysis->verdict pipeline runs offline for $0 and exercises the signal
path. The mock is a pipeline validator, NOT a scientific result (see DECISIONS D9).

DUAL-USE: prompts are supervisory (detect & escalate); no prompt coaches evasion.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secrets as secretstore  # noqa: E402

TYPOLOGY_TAGS = (
    "structuring", "layering", "trade_based", "mule_network",
    "shell_layering", "funnel_account", "rapid_passthrough", "cash_intensive_front",
)


class _GeminiVerdict(BaseModel):
    """Response schema for Gemini schema-constrained decoding. typology is a plain
    string ('none' or a tag); parse_strict coerces anything outside TYPOLOGY_TAGS to
    None, so the flag decision is unaffected."""
    suspicious: bool
    typology: str
    rationale: str

# ── prompt variants (supervisory; JSON-only) ────────────────────────────────
_SCHEMA_LINE = (
    'Respond with ONLY a JSON object and nothing else, in exactly this form: '
    '{"suspicious": true|false, "typology": <one of '
    + str(list(TYPOLOGY_TAGS)) + ' or null>, "rationale": "<=30 words"}. '
    'Set "suspicious" true if the activity should be escalated for AML review; '
    'otherwise false. "typology" names the closest laundering typology when '
    'suspicious, else null.'
)

_VARIANTS = {
    "v_terse": (
        "You are an AML transaction-screening analyst. Decide whether the described "
        "transaction sub-network is suspicious and should be escalated. " + _SCHEMA_LINE
    ),
    "v_fatf": (
        "You are an AML transaction-screening analyst applying the FATF typology "
        "catalogue (structuring/smurfing, layering, trade-based laundering, mule "
        "networks, shell-company layering, funnel accounts, rapid pass-through, "
        "cash-intensive fronts). Screen the described transaction sub-network for "
        "these typologies and decide whether to escalate. " + _SCHEMA_LINE
    ),
    "v_riskbased": (
        "You are an AML analyst applying a risk-based approach. Weigh KYC status, "
        "jurisdiction risk, transaction structure and economic rationale, then decide "
        "whether the described transaction sub-network warrants escalation. " + _SCHEMA_LINE
    ),
}

_USER_TEMPLATE = (
    "Screen the following transaction sub-network for money-laundering risk.\n\n"
    "{case}\n\n"
    "Return only the JSON verdict."
)


def system_prompt(variant: str) -> str:
    if variant not in _VARIANTS:
        raise KeyError(f"unknown prompt variant {variant!r}; have {sorted(_VARIANTS)}")
    return _VARIANTS[variant]


def build_user(serialized_case: str) -> str:
    return _USER_TEMPLATE.format(case=serialized_case)


def prompt_hash(system: str, user: str) -> str:
    return hashlib.sha256((system + "\n\x1e\n" + user).encode()).hexdigest()[:16]


# ── strict parse ────────────────────────────────────────────────────────────
@dataclass
class Verdict:
    suspicious: bool
    typology: str | None
    rationale: str


def _coerce_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str) and x.strip().lower() in ("true", "false"):
        return x.strip().lower() == "true"
    raise ValueError(f"suspicious not boolean: {x!r}")


_SUSPICIOUS_RE = re.compile(r'"suspicious"\s*:\s*(true|false)', re.IGNORECASE)
_TYPOLOGY_RE = re.compile(r'"typology"\s*:\s*"([a-z_]+)"', re.IGNORECASE)


def parse_strict(raw: str) -> Verdict:
    txt = raw.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", txt.strip())
    start = txt.find("{")
    if start == -1:
        raise ValueError(f"no JSON object in response: {raw[:160]!r}")
    try:
        obj, _ = json.JSONDecoder().raw_decode(txt[start:])
    except json.JSONDecodeError as e:
        # Salvage path: some models emit an UNAMBIGUOUS decision but malform the
        # JSON by leaving an unescaped quote inside the free-text rationale. We
        # recover the verbatim boolean decision (and typology if cleanly present)
        # by regex — we never invent a decision; if the boolean isn't literally
        # present, we still raise -> ERROR. (DECISIONS D14.)
        m = _SUSPICIOUS_RE.search(txt)
        if not m:
            raise ValueError(f"unparseable JSON and no literal 'suspicious': {e}")
        suspicious = m.group(1).lower() == "true"
        tm = _TYPOLOGY_RE.search(txt)
        typ = tm.group(1).lower() if tm else None
        if typ not in TYPOLOGY_TAGS:
            typ = None
        return Verdict(suspicious=suspicious, typology=typ,
                       rationale="(recovered from malformed JSON)")
    if "suspicious" not in obj:
        raise ValueError("missing 'suspicious'")
    suspicious = _coerce_bool(obj["suspicious"])
    typ = obj.get("typology")
    if isinstance(typ, str):
        typ = typ.strip().lower()
        if typ not in TYPOLOGY_TAGS:
            typ = None            # unknown typology -> null; the flag decision stands
    else:
        typ = None
    rationale = " ".join(str(obj.get("rationale", "")).split()[:30])
    return Verdict(suspicious=suspicious, typology=typ, rationale=rationale)


@dataclass
class AgentResult:
    ok: bool
    verdict: Verdict | None
    raw_response: str
    input_tokens: int
    output_tokens: int
    error: str | None
    prompt_hash: str
    key_id: str = ""


# ── deterministic mock screener ─────────────────────────────────────────────
def _u01(*parts) -> float:
    h = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:12], 16) / 0xFFFFFFFFFFFF


_DIFF_PEN = {"easy": 0.02, "medium": 0.16, "hard": 0.34}


def _mock_call(model_cfg, case: dict, variant: str, seed: int):
    """Deterministic fake verdict. Correlated misses via a shared per-case hardness
    (all models) plus an extra family-shared hardness (within-family), so
    within-family co-miss > cross-family co-miss > independence. Tuned for a
    pooled suspicious-miss rate ~30% (inside the 10-70% band)."""
    family = model_cfg.get("family", "x")
    cid = case["case_id"]
    label = case["label"]
    diff = case["difficulty"]

    # per-model detection skill (stable), spread so marginal miss rates differ.
    # Baseline tuned so the pooled suspicious-miss rate lands mid-band (~30-40%,
    # inside the pre-registered 10-70% measurable window).
    skill = 0.62 + 0.24 * _u01("skill", model_cfg.get("api_model", family))
    # shared latent hardness (drives cross-model correlation)
    h_case = _u01("hard", cid)
    # family-shared extra hardness (drives within-family extra correlation)
    h_fam = _u01("famhard", family, cid)
    noise = (_u01("noise", model_cfg.get("api_model", family), variant, seed, cid) - 0.5) * 0.10

    if label == "suspicious":
        score = skill - 0.62 * h_case - 0.28 * h_fam - _DIFF_PEN[diff] + noise
        suspicious = score > 0.0                       # flag if score positive; else MISS
        typ = case.get("typology") if suspicious else None
        rationale = "mock: escalate" if suspicious else "mock: no escalation"
    else:
        # benign hard-negatives: occasional false positive, rate rises with difficulty
        fp_score = 0.30 * h_case + _DIFF_PEN[diff] - skill * 0.4 + noise
        suspicious = fp_score > 0.15
        typ = "structuring" if suspicious else None
        rationale = "mock: benign" if not suspicious else "mock: flag(benign)"

    raw = json.dumps({"suspicious": bool(suspicious), "typology": typ, "rationale": rationale})
    return raw, 60, 16


# ── live provider router (OpenAI-compatible + Gemini) with key-pool failover ─
_POOLS: dict[str, dict] = {}
_POOLS_LOCK = threading.Lock()
_CLIENTS: dict[tuple, Any] = {}
_CLIENTS_LOCK = threading.Lock()


class AllKeysExhausted(RuntimeError):
    pass


_BENCH_COOLDOWN = 30.0   # seconds a rate-limited key is benched before it recovers


def _pool(provider: str) -> dict:
    with _POOLS_LOCK:
        p = _POOLS.get(provider)
        if p is None:
            keys = secretstore.get_pool(provider)
            p = {"keys": keys, "idx": 0, "benched": {}}   # key_id -> recover_at (monotonic)
            _POOLS[provider] = p
        return p


def _next_key(provider: str) -> tuple[str, int]:
    """Round-robin the pool, skipping keys still in cooldown. Benching is TEMPORARY:
    a key recovers after _BENCH_COOLDOWN, so a rate-limit burst pauses rather than
    permanently killing the pool. Raises AllKeysExhausted only if EVERY key is still
    cooling down right now (the caller then backs off and retries)."""
    import time
    p = _pool(provider)
    with _POOLS_LOCK:
        now = time.monotonic()
        n = len(p["keys"])
        for _ in range(n):
            i = p["idx"] % n
            p["idx"] += 1
            recover_at = p["benched"].get(i)
            if recover_at is None or recover_at <= now:
                p["benched"].pop(i, None)
                return p["keys"][i], i
        raise AllKeysExhausted(f"all {n} {provider} keys rate-limited (cooling down)")


def _bench_key(provider: str, key_id: int) -> None:
    import time
    p = _pool(provider)
    with _POOLS_LOCK:
        p["benched"][key_id] = time.monotonic() + _BENCH_COOLDOWN


def _client(provider: str, base_url: str | None, api_key: str, key_id: int):
    ck = (provider, key_id)
    with _CLIENTS_LOCK:
        c = _CLIENTS.get(ck)
        if c is not None:
            return c
        if provider in ("openai", "xai"):
            from openai import OpenAI
            kwargs = {"api_key": api_key, "max_retries": 0}
            if base_url:
                kwargs["base_url"] = base_url
            elif provider == "xai":
                kwargs["base_url"] = "https://api.x.ai/v1"
            c = OpenAI(**kwargs)
        elif provider in ("gemini", "google"):
            from google import genai
            c = genai.Client(api_key=api_key)
        else:
            raise ValueError(f"unknown provider {provider!r}")
        _CLIENTS[ck] = c
        return c


def _is_ratelimit(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in ("429", "rate limit", "rate_limit", "quota",
                                "resource_exhausted", "insufficient_quota"))


def _openai_compatible(mcfg, system, user, temperature, seed):
    provider = mcfg["provider"]
    last = None
    for _attempt in range(max(1, len(_pool(provider)["keys"]))):
        try:
            api_key, key_id = _next_key(provider)
        except AllKeysExhausted as e:
            raise RuntimeError(str(e)) from e
        client = _client(provider, mcfg.get("base_url"), api_key, key_id)
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        base = {"model": mcfg["api_model"], "messages": msgs,
                "response_format": {"type": "json_object"}}
        if seed is not None:
            base["seed"] = seed
        if mcfg.get("reasoning_effort"):
            base["reasoning_effort"] = mcfg["reasoning_effort"]
        max_out = int(mcfg.get("max_tokens", 256))
        for tok_param, with_temp in (("max_completion_tokens", True),
                                     ("max_completion_tokens", False),
                                     ("max_tokens", True)):
            kwargs = dict(base); kwargs[tok_param] = max_out
            if with_temp:
                kwargs["temperature"] = temperature
            try:
                resp = client.chat.completions.create(**kwargs)
            except Exception as e:
                last = e; m = str(e).lower()
                if _is_ratelimit(m):
                    _bench_key(provider, key_id); break            # rotate to next key
                if "reasoning_effort" in m:
                    base.pop("reasoning_effort", None); continue
                if "response_format" in m:
                    base.pop("response_format", None); continue
                if any(k in m for k in ("temperature", "max_tokens", "max_completion",
                                        "unsupported", "unknown parameter")):
                    continue
                raise
            u = resp.usage
            content = resp.choices[0].message.content or ""
            if content.strip():
                return content, u.prompt_tokens, u.completion_tokens, str(key_id)
            last = RuntimeError(f"empty content (finish={resp.choices[0].finish_reason})")
    raise last or RuntimeError("all openai-compatible attempts failed")


def _call_gemini(mcfg, system, user, temperature, seed):
    from google.genai import types
    provider = "gemini"
    last = None
    for _attempt in range(max(1, len(_pool(provider)["keys"]))):
        try:
            api_key, key_id = _next_key(provider)
        except AllKeysExhausted as e:
            raise RuntimeError(str(e)) from e
        client = _client(provider, None, api_key, key_id)
        base = {"system_instruction": system, "temperature": temperature,
                "max_output_tokens": int(mcfg.get("max_tokens", 256)),
                "response_mime_type": "application/json"}
        # Only set thinking_config when the model declares a budget. thinking_budget=0
        # disables thinking (cheap, for Flash); models that REQUIRE thinking (e.g.
        # Gemini Pro) must omit it (thinking_budget=None) and use their default.
        tb = mcfg.get("thinking_budget")
        if tb is not None:
            try:
                base["thinking_config"] = types.ThinkingConfig(thinking_budget=int(tb))
            except Exception:
                pass
        if seed is not None:
            base["seed"] = seed
        # Try schema-constrained decoding first (guarantees valid JSON with escaped
        # string fields — fixes Gemini's unescaped-quote-in-rationale parse errors,
        # DECISIONS D14). Fall back WITHOUT the schema if the installed SDK/model
        # rejects it (the hardened parser then recovers the flag).
        for use_schema in (True, False):
            gc = dict(base)
            if use_schema:
                gc["response_schema"] = _GeminiVerdict
            try:
                resp = client.models.generate_content(
                    model=mcfg["api_model"], contents=user,
                    config=types.GenerateContentConfig(**gc))
            except Exception as e:
                last = e
                if _is_ratelimit(str(e)):
                    _bench_key(provider, key_id); break            # rotate key
                if use_schema and any(k in str(e).lower() for k in
                                      ("schema", "response_schema", "unknown", "invalid")):
                    continue                                        # retry without schema
                raise
            um = resp.usage_metadata
            return (resp.text or ""), um.prompt_token_count, (um.candidates_token_count or 0), str(key_id)
    raise last or RuntimeError("all gemini attempts failed")


def call_model(mcfg, system, user, temperature, seed):
    provider = mcfg["provider"]
    if provider in ("openai", "xai"):
        return _openai_compatible(mcfg, system, user, temperature, seed)
    if provider in ("gemini", "google"):
        return _call_gemini(mcfg, system, user, temperature, seed)
    raise ValueError(f"unknown provider {provider!r}")


def run_agent(model_cfg: dict, case: dict, variant: str, temperature: float,
              seed: int) -> AgentResult:
    system = system_prompt(variant)
    user = build_user(case["serialized"])
    ph = prompt_hash(system, user)
    key_id = ""
    try:
        if os.environ.get("PILOT_MOCK") == "1":
            raw, in_tok, out_tok = _mock_call(model_cfg, case, variant, seed)
        else:
            raw, in_tok, out_tok, key_id = call_model(model_cfg, system, user, temperature, seed)
    except Exception as e:
        return AgentResult(False, None, "", 0, 0, f"{type(e).__name__}: {e}", ph, key_id)
    try:
        v = parse_strict(raw)
    except Exception as e:
        return AgentResult(False, None, raw, in_tok, out_tok, f"parse: {e}", ph, key_id)
    return AgentResult(True, v, raw, in_tok, out_tok, None, ph, key_id)
