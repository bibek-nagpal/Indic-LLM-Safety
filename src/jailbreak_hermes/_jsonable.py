"""Shared JSON-serialisation helper for dataclass-friendly dicts."""

from __future__ import annotations

import dataclasses
from typing import Any


def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclass instances to plain dicts."""
    if dataclasses.is_dataclass(obj):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
