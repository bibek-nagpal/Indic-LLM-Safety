"""ModelRunner — fires a fixed prompt at one or more target models
with frozen generation settings. Per the paper, target settings are
NOT negotiable: temperature=0, fixed system prompt.

Both sync (run_one / run_pair) and async (arun_one / arun_pair)
flavours are provided; V3's worker pool uses the async ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .openrouter_client import achat, chat


# Empty system prompt by design — treat target as a black box.
TARGET_SYSTEM_PROMPT = ""


@dataclass
class ModelResponse:
    model: str
    prompt: str
    language: str  # "en" | "rh"
    content: str
    finish_reason: str | None = None
    error: str | None = None


@dataclass
class ModelPairResponses:
    model: str
    english: ModelResponse
    romanized_hindi: ModelResponse
    meta: dict = field(default_factory=dict)


def _messages(prompt: str, system_prompt: str) -> list[dict]:
    msgs: list[dict] = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def run_one(
    model: str,
    prompt: str,
    *,
    language: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    system_prompt: str = TARGET_SYSTEM_PROMPT,
) -> ModelResponse:
    try:
        reply = chat(
            model, _messages(prompt, system_prompt),
            temperature=temperature, max_tokens=max_tokens,
        )
        return ModelResponse(
            model=model, prompt=prompt, language=language,
            content=reply.content, finish_reason=reply.finish_reason,
        )
    except Exception as exc:  # noqa: BLE001
        return ModelResponse(
            model=model, prompt=prompt, language=language,
            content="", error=str(exc),
        )


def run_pair(
    model: str,
    english_prompt: str,
    romanized_hindi_prompt: str,
    *,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> ModelPairResponses:
    return ModelPairResponses(
        model=model,
        english=run_one(model, english_prompt, language="en",
                         max_tokens=max_tokens, temperature=temperature),
        romanized_hindi=run_one(model, romanized_hindi_prompt, language="rh",
                                 max_tokens=max_tokens, temperature=temperature),
    )


async def arun_one(
    model: str,
    prompt: str,
    *,
    language: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    system_prompt: str = TARGET_SYSTEM_PROMPT,
    client=None,
) -> ModelResponse:
    try:
        reply = await achat(
            model, _messages(prompt, system_prompt),
            temperature=temperature, max_tokens=max_tokens, client=client,
            purpose="target_model",
        )
        return ModelResponse(
            model=model, prompt=prompt, language=language,
            content=reply.content, finish_reason=reply.finish_reason,
        )
    except Exception as exc:  # noqa: BLE001
        return ModelResponse(
            model=model, prompt=prompt, language=language,
            content="", error=str(exc),
        )


async def arun_pair(
    model: str,
    english_prompt: str,
    romanized_hindi_prompt: str,
    *,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    client=None,
) -> ModelPairResponses:
    import asyncio
    en_task = asyncio.create_task(arun_one(
        model, english_prompt, language="en",
        max_tokens=max_tokens, temperature=temperature, client=client))
    rh_task = asyncio.create_task(arun_one(
        model, romanized_hindi_prompt, language="rh",
        max_tokens=max_tokens, temperature=temperature, client=client))
    en, rh = await asyncio.gather(en_task, rh_task)
    return ModelPairResponses(model=model, english=en, romanized_hindi=rh)
