"""Robust JSON extraction from chatty / reasoning-model outputs.

Reasoning models (Nemotron, Qwen3 in /think mode, DeepSeek-R1, ...)
emit a chain-of-thought into the same `content` field. That CoT often
contains its own `{` and `}` characters in code snippets or commentary,
so a naive `text[text.find('{') : text.rfind('}') + 1]` slice doesn't
work: it can grab a `{` from the reasoning and a `}` from the final
JSON, producing a garbage substring.

Strategy used here:
  1. Strip Markdown code fences (```json ... ```).
  2. Try `json.loads` on the whole text.
  3. Use `json.JSONDecoder().raw_decode` to walk over the string left
     to right finding every parseable JSON object; return the LAST one
     that has at least one key in `expected_keys` (if provided) or
     just the last one parsed.
"""

from __future__ import annotations

import json
import re
from typing import Iterable, Optional


_CODE_FENCE = re.compile(r"```(?:json|JSON)?\s*\n?(.*?)```", re.S)


def _strip_fences(text: str) -> str:
    m = list(_CODE_FENCE.finditer(text))
    if m:
        # Return the last fenced block (model often emits the final
        # answer last, after thinking aloud above).
        return m[-1].group(1).strip()
    return text


def _iter_json_objects(text: str):
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n:
        # Move to the next opening brace
        brace = text.find("{", idx)
        if brace == -1:
            return
        try:
            obj, end = decoder.raw_decode(text, brace)
        except json.JSONDecodeError:
            idx = brace + 1
            continue
        yield obj
        idx = end


def loads(text: str, *, expected_keys: Iterable[str] | None = None) -> dict:
    """Best-effort JSON object extraction.

    Raises json.JSONDecodeError if no parseable JSON object is found.
    """
    if not text or not text.strip():
        raise json.JSONDecodeError("empty", text or "", 0)

    cleaned = _strip_fences(text).strip()
    # Fast path
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    expected = set(expected_keys or ())
    best: Optional[dict] = None
    last: Optional[dict] = None
    for obj in _iter_json_objects(cleaned):
        if not isinstance(obj, dict):
            continue
        last = obj
        if expected and set(obj.keys()) & expected:
            best = obj  # keep the latest matching
    if best is not None:
        return best
    if last is not None:
        return last
    raise json.JSONDecodeError("no JSON object found", cleaned, 0)
