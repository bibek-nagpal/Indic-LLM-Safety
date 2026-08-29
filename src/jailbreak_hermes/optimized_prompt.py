"""Read-only loader for GEPA-evolved generator instructions.

Kept separate from ``run_gepa`` so normal bank/target runs do not require DSPy
at import time.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional


def load_optimized_instruction(run_id: str | None = None,
                                root: str | Path = "prompts/optimized",
                                *, require_v2: bool = False) -> Optional[str]:
    root_p = Path(root)
    if not root_p.exists():
        return None
    def eligible(d: Path) -> bool:
        if not require_v2:
            return True
        m = d / "optimization_manifest.json"
        if not m.exists():
            return False
        try:
            import json
            obj = json.loads(m.read_text(encoding="utf-8"))
            return (
                obj.get("schema_version") == 2
                and obj.get("target_model_signal_used") is False
                and obj.get("objective") == "complete_target_independent_probe_validity"
            )
        except Exception:
            return False

    if run_id:
        d = root_p / run_id
        p = d / "generator.txt"
        return p.read_text(encoding="utf-8") if p.exists() and eligible(d) else None
    dirs = [d for d in sorted(root_p.glob("gepa_*")) if eligible(d)]
    if not dirs:
        return None
    p = dirs[-1] / "generator.txt"
    return p.read_text(encoding="utf-8") if p.exists() else None
