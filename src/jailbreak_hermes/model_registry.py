"""Model registry — the single place where logical roles map to
OpenRouter model IDs.

Modules MUST import `get_model("judge")` / `get_model("target")[...]`
etc., not hardcode model strings. That way swapping providers (or
upgrading to paid tier) is a one-file change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


_ROLES_WITH_FALLBACK = {
    "judge_model",
    "summarizer_model",
    "generator_model",
    "equivalence_model",
    "secondary_equivalence_model",
    "gepa_reflection_model",
}


@dataclass
class ModelRegistry:
    orchestrator: str
    judge_model: str
    summarizer_model: str
    generator_model: str
    equivalence_model: str
    secondary_equivalence_model: str
    gepa_reflection_model: str
    fallback_judge_model: str | None = None
    target_models: list[str] = field(default_factory=list)
    max_orchestrator_tokens: int = 1024
    max_target_tokens: int = 1024
    max_judge_tokens: int = 800
    target_temperature: float = 0.0
    orchestrator_temperature: float = 0.0
    generator_temperature: float = 0.4

    def for_role(self, role: str) -> str:
        """role in {orchestrator, judge, summarizer, generator,
        equivalence, secondary_equivalence, gepa_reflection}."""
        attr = role if role.endswith("_model") or role == "orchestrator" else f"{role}_model"
        return getattr(self, attr)


_DEFAULT_PATH = Path("configs/models.yaml")
_CACHE: dict[str, ModelRegistry] = {}


def load(path: str | Path | None = None) -> ModelRegistry:
    p = Path(path) if path else _DEFAULT_PATH
    key = str(p.resolve())
    if key in _CACHE:
        return _CACHE[key]
    data = yaml.safe_load(p.read_text())
    orchestrator = data.get("orchestrator")
    if not orchestrator:
        raise ValueError(f"{p}: missing required key 'orchestrator'")
    resolved = {"orchestrator": orchestrator}
    for role in _ROLES_WITH_FALLBACK:
        val = data.get(role)
        resolved[role] = val or orchestrator
    resolved["fallback_judge_model"] = data.get("fallback_judge_model")
    resolved["target_models"] = list(data.get("target_models") or [])
    if not resolved["target_models"]:
        raise ValueError(f"{p}: target_models must be a non-empty list")
    # passthrough numeric/string knobs
    for opt_field in (
        "max_orchestrator_tokens", "max_target_tokens", "max_judge_tokens",
        "target_temperature", "orchestrator_temperature", "generator_temperature",
    ):
        if opt_field in data:
            resolved[opt_field] = data[opt_field]
    reg = ModelRegistry(**resolved)
    _CACHE[key] = reg
    return reg


def clear_cache() -> None:
    _CACHE.clear()


def env_override_target_models() -> list[str] | None:
    """Optional env override: JBH_TARGET_MODELS=comma,separated,list"""
    val = os.environ.get("JBH_TARGET_MODELS")
    if not val:
        return None
    return [s.strip() for s in val.split(",") if s.strip()]
