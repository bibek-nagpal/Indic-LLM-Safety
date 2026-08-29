"""OpenRouter chat-completion client (sync + async).

Sync `chat()` and async `achat()` share the same retry / backoff /
error-classification logic via `_post_with_retry`. The original
hermes-agent ships a richer client at `tools/openrouter_client.py`,
but it pulls in the full `agent.auxiliary_client` provider-routing
stack. We only need chat completions.

Retry policy
------------
Rate limits (429) and transient errors (502/503/504, network) use
*separate* retry budgets, because they mean different things:

- 429 (rate limit) : wait it out. Long, near-constant gaps (default
  ~60-120s, honoring any ``Retry-After`` header) for up to
  ``JBH_RATELIMIT_MAX_RETRIES`` attempts (default 60 → ~2h of waiting).
  Paid models effectively never hit this; the only free-tier model in
  the lineup (Nemotron) can, and we want to ride out its per-minute
  window rather than drop the data point.
- 502 / 503 / 504 / network : jittered exponential backoff (cap
  ``JBH_BACKOFF_CAP``, default 30s) up to ``JBH_MAX_RETRIES`` (default 6).
- 402 (insufficient credits) : raised immediately — waiting won't help.
- any other status            : raised immediately.

All knobs are env-overridable so the parallel runner can be tuned
without code changes:
  JBH_MAX_RETRIES, JBH_BACKOFF_CAP,
  JBH_RATELIMIT_MAX_RETRIES, JBH_RATELIMIT_WAIT, JBH_RATELIMIT_WAIT_CAP

Reasoning models (Nemotron, Qwen3) emit a chain of thought that lives
in the same `content` field. Callers must allow enough `max_tokens`
or the visible answer is truncated and `finish_reason == 'length'`.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
import json
from pathlib import Path
from dataclasses import dataclass

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_TIMEOUT = 180.0
RATE_LIMIT_STATUS = 429
# 429 is handled on its own (wait-it-out) path, NOT in this set.
RETRYABLE_STATUS = {502, 503, 504}

_ACCOUNTING_SESSION = time.strftime("%Y%m%d_%H%M%S")
_ACCOUNTING_ROOT = Path(os.environ.get("JBH_ACCOUNTING_ROOT", "accounting"))
_ACCOUNTING_PATH = _ACCOUNTING_ROOT / f"api_calls_{_ACCOUNTING_SESSION}.jsonl"


def _usage_record(data: dict, requested_model: str, purpose: str, status: str = "success") -> dict:
    usage = data.get("usage") if isinstance(data, dict) else {}
    usage = usage if isinstance(usage, dict) else {}
    # OpenRouter/LiteLLM-compatible response variants.
    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    cost = usage.get("cost")
    if cost is None:
        cost = data.get("cost") if isinstance(data, dict) else None
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "requested_model": requested_model,
        "resolved_model": data.get("model", requested_model) if isinstance(data, dict) else requested_model,
        "purpose": purpose,
        "status": status,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost,
        "usage_raw": usage,
        "request_id": data.get("id") if isinstance(data, dict) else None,
    }


def _account(record: dict) -> None:
    try:
        _ACCOUNTING_ROOT.mkdir(parents=True, exist_ok=True)
        with _ACCOUNTING_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Accounting must never corrupt an otherwise valid scientific call.
        pass


def accounting_summary() -> dict:
    if not _ACCOUNTING_PATH.exists():
        return {"path": str(_ACCOUNTING_PATH), "calls": 0, "successful_calls": 0,
                "failed_calls": 0, "known_cost_usd": 0.0, "by_model": {}}
    rows = []
    for line in _ACCOUNTING_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    by_model = {}
    known_cost = 0.0
    for r in rows:
        m = r.get("requested_model", "unknown")
        b = by_model.setdefault(m, {"calls": 0, "successful": 0, "failed": 0,
                                    "prompt_tokens": 0, "completion_tokens": 0,
                                    "known_cost_usd": 0.0})
        b["calls"] += 1
        b["successful"] += int(r.get("status") == "success")
        b["failed"] += int(r.get("status") != "success")
        b["prompt_tokens"] += int(r.get("prompt_tokens") or 0)
        b["completion_tokens"] += int(r.get("completion_tokens") or 0)
        if r.get("cost_usd") is not None:
            try:
                c = float(r["cost_usd"])
                b["known_cost_usd"] += c
                known_cost += c
            except Exception:
                pass
    return {
        "path": str(_ACCOUNTING_PATH),
        "calls": len(rows),
        "successful_calls": sum(r.get("status") == "success" for r in rows),
        "failed_calls": sum(r.get("status") != "success" for r in rows),
        "known_cost_usd": known_cost,
        "by_model": by_model,
    }


def write_accounting_summary(path: str | Path | None = None) -> Path:
    out = Path(path) if path else _ACCOUNTING_PATH.with_name(_ACCOUNTING_PATH.stem + "_summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(accounting_summary(), indent=2), encoding="utf-8")
    return out


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.environ.get(name) or "").strip() or default)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float((os.environ.get(name) or "").strip() or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int        # transient 5xx + network errors
    backoff_cap: float      # cap for 5xx/network exponential backoff (s)
    rl_max_retries: int     # 429 attempts (wait out the limit window)
    rl_wait: float          # base gap between 429 retries (s)
    rl_wait_cap: float      # cap on any single 429 gap (s)


def _retry_config() -> RetryConfig:
    """Read retry tuning from the environment (with sane paid-tier defaults).
    Resolved per-call so a long-running parallel run can be retuned by
    exporting new values without restarting in-flight Python is not needed —
    each new batch process picks them up."""
    return RetryConfig(
        max_retries=_env_int("JBH_MAX_RETRIES", 6),
        backoff_cap=_env_float("JBH_BACKOFF_CAP", 30.0),
        rl_max_retries=_env_int("JBH_RATELIMIT_MAX_RETRIES", 60),
        rl_wait=_env_float("JBH_RATELIMIT_WAIT", 60.0),
        rl_wait_cap=_env_float("JBH_RATELIMIT_WAIT_CAP", 120.0),
    )


class OpenRouterError(RuntimeError):
    pass


class OpenRouterCreditError(OpenRouterError):
    """Raised on HTTP 402 — the account has no credits for the chosen model."""


class OpenRouterRateLimitError(OpenRouterError):
    """Raised after we exhausted retries on 429s."""


@dataclass
class ChatResponse:
    model: str
    content: str
    finish_reason: str | None
    raw: dict


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY environment variable not set")
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Soham-Kumar/jailbreak_hermes",
        "X-Title": "jailbreak_hermes safety eval",
    }


def _payload(model: str, messages: list[dict], temperature: float, max_tokens: int) -> dict:
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        # Some upstreams (DeepSeek-R1/v4, OpenAI o-series, Nemotron-reasoning)
        # hide the model's chain of thought by default. We want it surfaced so
        # `_parse` can fall back to it when `message.content` is empty.
        "include_reasoning": True,
    }


def _parse(data: dict, model: str) -> ChatResponse:
    """Extract the final assistant text from OpenRouter's response.

    For reasoning models, the upstream sometimes returns:
        choices[0].message.content      = ""
        choices[0].message.reasoning    = "long CoT...final answer..."
    or
        choices[0].message.reasoning_content = "..."
    When `content` is empty, we fall back to `reasoning` /
    `reasoning_content` so the caller (judge / generator / target) sees a
    usable string instead of "".
    """
    if "error" in data and not data.get("choices"):
        raise OpenRouterError(f"OpenRouter error: {data['error']}")
    try:
        choice = data["choices"][0]
        msg = choice["message"]
        finish_reason = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError(f"Unexpected OpenRouter payload: {data}") from exc

    content = msg.get("content") or ""
    if not content.strip():
        # Try the common reasoning-field names in order
        for k in ("reasoning", "reasoning_content"):
            candidate = msg.get(k) or ""
            if isinstance(candidate, str) and candidate.strip():
                content = candidate
                break
    return ChatResponse(
        model=data.get("model", model),
        content=content,
        finish_reason=finish_reason,
        raw=data,
    )


def _classify_status(status: int, body_text: str) -> None:
    """Raise for terminal statuses. 429 and 5xx-retryable return cleanly
    so the caller can route them to the right wait path."""
    if status == 402:
        raise OpenRouterCreditError(f"OpenRouter 402 (no credits): {body_text[:300]}")
    if status == RATE_LIMIT_STATUS:
        return
    if status not in RETRYABLE_STATUS:
        raise OpenRouterError(f"OpenRouter {status}: {body_text[:500]}")


def _backoff_seconds(attempt: int, base: float = 2.0, cap: float = 30.0) -> float:
    # Jittered exponential backoff. attempt is 0-indexed.
    expo = min(cap, base * (2 ** attempt))
    return expo * (0.5 + random.random() * 0.5)


def _parse_retry_after(headers) -> float | None:
    """Honor a numeric `Retry-After` (seconds). HTTP-date form is ignored —
    we fall back to our own schedule rather than parse dates."""
    val = headers.get("retry-after") or headers.get("Retry-After")
    if not val:
        return None
    try:
        secs = float(val)
        return secs if secs >= 0 else None
    except (TypeError, ValueError):
        return None


def _ratelimit_wait(attempt: int, retry_after: float | None, cfg: RetryConfig) -> float:
    """Gap before the next 429 retry. Prefer the server's Retry-After;
    otherwise a near-constant wait (base..cap) with jitter so concurrent
    workers don't all retry on the same tick (thundering herd)."""
    if retry_after is not None and retry_after > 0:
        # Respect the server, plus a little slack and jitter, but never
        # block absurdly long on a single hint.
        return min(retry_after, cfg.rl_wait_cap) + random.random() * 5.0
    base = min(cfg.rl_wait_cap, cfg.rl_wait * (1.0 + 0.25 * attempt))
    return base * (0.85 + random.random() * 0.3)


# sync

def chat(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int | None = None,
    purpose: str = "unspecified",
) -> ChatResponse:
    cfg = _retry_config()
    max_retries = cfg.max_retries if max_retries is None else max_retries
    payload = _payload(model, messages, temperature, max_tokens)
    last_status = None
    last_body = ""
    rl_attempt = 0    # 429s — wait-it-out budget
    err_attempt = 0   # 5xx / network — exponential-backoff budget
    with httpx.Client(timeout=timeout) as client:
        while True:
            try:
                resp = client.post(OPENROUTER_URL, headers=_headers(), json=payload)
            except httpx.HTTPError as exc:
                if err_attempt >= max_retries:
                    raise OpenRouterError(
                        f"network error after {err_attempt+1} attempts: {exc}") from exc
                time.sleep(_backoff_seconds(err_attempt, cap=cfg.backoff_cap))
                err_attempt += 1
                continue
            if resp.status_code < 300:
                data = resp.json()
                _account(_usage_record(data, model, purpose, "success"))
                return _parse(data, model)
            last_status = resp.status_code
            last_body = resp.text
            if resp.status_code == 402 or (resp.status_code != RATE_LIMIT_STATUS and resp.status_code not in RETRYABLE_STATUS):
                _account({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "requested_model": model,
                          "resolved_model": model, "purpose": purpose, "status": f"http_{resp.status_code}",
                          "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
                          "cost_usd": None, "usage_raw": {}, "request_id": None})
            _classify_status(resp.status_code, resp.text)  # raises on 402 / terminal
            if resp.status_code == RATE_LIMIT_STATUS:
                if rl_attempt >= cfg.rl_max_retries:
                    break
                time.sleep(_ratelimit_wait(rl_attempt, _parse_retry_after(resp.headers), cfg))
                rl_attempt += 1
                continue
            if err_attempt >= max_retries:
                break
            time.sleep(_backoff_seconds(err_attempt, cap=cfg.backoff_cap))
            err_attempt += 1
    raise OpenRouterRateLimitError(
        f"OpenRouter retried out (last {last_status}): {last_body[:500]}"
    )


# async

async def achat(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int | None = None,
    client: httpx.AsyncClient | None = None,
    purpose: str = "unspecified",
) -> ChatResponse:
    cfg = _retry_config()
    max_retries = cfg.max_retries if max_retries is None else max_retries
    payload = _payload(model, messages, temperature, max_tokens)
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=timeout)
    last_status = None
    last_body = ""
    rl_attempt = 0    # 429s — wait-it-out budget
    err_attempt = 0   # 5xx / network — exponential-backoff budget
    try:
        while True:
            try:
                resp = await client.post(OPENROUTER_URL, headers=_headers(), json=payload)
            except httpx.HTTPError as exc:
                if err_attempt >= max_retries:
                    raise OpenRouterError(
                        f"network error after {err_attempt+1} attempts: {exc}") from exc
                await asyncio.sleep(_backoff_seconds(err_attempt, cap=cfg.backoff_cap))
                err_attempt += 1
                continue
            if resp.status_code < 300:
                data = resp.json()
                _account(_usage_record(data, model, purpose, "success"))
                return _parse(data, model)
            last_status = resp.status_code
            last_body = resp.text
            if resp.status_code == 402 or (resp.status_code != RATE_LIMIT_STATUS and resp.status_code not in RETRYABLE_STATUS):
                _account({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "requested_model": model,
                          "resolved_model": model, "purpose": purpose, "status": f"http_{resp.status_code}",
                          "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
                          "cost_usd": None, "usage_raw": {}, "request_id": None})
            _classify_status(resp.status_code, resp.text)  # raises on 402 / terminal
            if resp.status_code == RATE_LIMIT_STATUS:
                if rl_attempt >= cfg.rl_max_retries:
                    break
                await asyncio.sleep(
                    _ratelimit_wait(rl_attempt, _parse_retry_after(resp.headers), cfg))
                rl_attempt += 1
                continue
            if err_attempt >= max_retries:
                break
            await asyncio.sleep(_backoff_seconds(err_attempt, cap=cfg.backoff_cap))
            err_attempt += 1
        raise OpenRouterRateLimitError(
            f"OpenRouter retried out (last {last_status}): {last_body[:500]}"
        )
    finally:
        if own_client:
            await client.aclose()
