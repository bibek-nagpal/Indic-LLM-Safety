"""CategorySpec loader.

A category spec is a YAML file under `configs/categories/<id>.yaml`
describing a harm category, allowed/disallowed model behaviour, and
which evaluation axes apply. The harness loads one spec per run and
uses it to constrain candidate generation and judging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class CategorySpec:
    id: str
    definition: str
    indian_context_required: bool = True
    allowed_outputs: list[str] = field(default_factory=list)
    disallowed_outputs: list[str] = field(default_factory=list)
    evaluation_axis: list[str] = field(default_factory=list)
    gate_questions: dict[str, str] = field(default_factory=dict)
    seed_examples: list[dict] = field(default_factory=list)
    notes: str = ""


def load(path: str | Path) -> CategorySpec:
    p = Path(path)
    data = yaml.safe_load(p.read_text())
    if "id" not in data:
        raise ValueError(f"category spec {p} missing 'id'")
    return CategorySpec(**{k: v for k, v in data.items() if k in CategorySpec.__dataclass_fields__})


def load_by_id(category_id: str, root: str | Path = "configs/categories") -> CategorySpec:
    root_p = Path(root)
    candidate = root_p / f"{category_id}.yaml"
    if not candidate.exists():
        available = sorted(p.stem for p in root_p.glob("*.yaml"))
        raise FileNotFoundError(
            f"no spec for '{category_id}' in {root_p}. available: {available}"
        )
    return load(candidate)


def list_categories(root: str | Path = "configs/categories") -> list[str]:
    return sorted(p.stem for p in Path(root).glob("*.yaml"))
