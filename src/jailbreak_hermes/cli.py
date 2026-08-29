"""CLI entry point — `jbh run`, `jbh run-async`, `jbh gepa`,
`jbh compact-memory`, `jbh list-categories`, `jbh show-models`."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
import yaml
from dotenv import load_dotenv

from . import category_spec, model_registry
from .run import RunConfig, run_batch


@click.group()
def main() -> None:
    """jailbreak_hermes — paired EN/RH safety-evaluation harness."""
    load_dotenv()


@main.command("list-categories")
@click.option("--root", default="configs/categories", show_default=True)
def list_categories(root: str) -> None:
    for cat in category_spec.list_categories(root=root):
        click.echo(cat)


@main.command("show-models")
@click.option("--models-config", default="configs/models.yaml", show_default=True)
def show_models(models_config: str) -> None:
    """Print the resolved model registry."""
    reg = model_registry.load(models_config)
    click.echo(yaml.safe_dump({
        "orchestrator": reg.orchestrator,
        "judge_model": reg.judge_model,
        "summarizer_model": reg.summarizer_model,
        "generator_model": reg.generator_model,
        "equivalence_model": reg.equivalence_model,
        "secondary_equivalence_model": reg.secondary_equivalence_model,
        "gepa_reflection_model": reg.gepa_reflection_model,
        "target_models": reg.target_models,
    }, sort_keys=False))


def _build_overrides(category, strategies, n_candidates, skip_retrieval,
                     models_config, gepa_enabled, gepa_budget, v3_concurrency,
                     no_escalation, output_prefix) -> dict:
    overrides: dict = {}
    if category:
        overrides["category"] = category
    if strategies:
        overrides["strategies"] = [s.strip() for s in strategies.split(",") if s.strip()]
    if n_candidates is not None:
        overrides["n_candidates_per_strategy"] = n_candidates
    if skip_retrieval:
        overrides["skip_retrieval"] = True
    if models_config:
        overrides["models_config"] = models_config
    if gepa_enabled:
        overrides["gepa_enabled"] = True
    if gepa_budget is not None:
        overrides["gepa_budget"] = gepa_budget
    if v3_concurrency is not None:
        overrides["v3_concurrency"] = v3_concurrency
    if no_escalation:
        overrides["escalate_on_no_flips"] = False
    if output_prefix:
        overrides["run_id_prefix"] = output_prefix
    return overrides


_COMMON_OPTIONS = [
    click.option("--config", "config_path", default="configs/run.yaml", show_default=True),
    click.option("--category", default=None),
    click.option("--strategies", default=None,
                 help="Comma-separated strategy ids."),
    click.option("--n-candidates", default=None, type=int),
    click.option("--skip-retrieval", is_flag=True, default=False),
    click.option("--models-config", default=None,
                 help="Override path to models.yaml."),
    click.option("--gepa-enabled/--no-gepa", default=None),
    click.option("--gepa-budget", default=None, type=int),
    click.option("--v3-concurrency", default=None, type=int),
    click.option("--no-escalation", "no_escalation", is_flag=True, default=False,
                 help="Disable niche escalation when round 1 produces zero flips."),
    click.option("--output-prefix", "output_prefix", default=None,
                 help="Prefix for the run output directory (e.g. 'exp2_violence')."),
]


def _add_common(cmd):
    for opt in reversed(_COMMON_OPTIONS):
        cmd = opt(cmd)
    return cmd


@main.command("run")
@_add_common
def run_cmd(config_path, category, strategies, n_candidates, skip_retrieval,
            models_config, gepa_enabled, gepa_budget, v3_concurrency,
            no_escalation, output_prefix):
    """V1: synchronous batch run."""
    overrides = _build_overrides(category, strategies, n_candidates, skip_retrieval,
                                  models_config, gepa_enabled, gepa_budget, v3_concurrency,
                                  no_escalation, output_prefix)
    cfg = RunConfig.from_yaml(config_path, overrides=overrides)
    out = run_batch(cfg)
    click.echo(f"\nDone. Outputs in: {out}")


@main.command("run-async")
@_add_common
def run_async_cmd(config_path, category, strategies, n_candidates, skip_retrieval,
                   models_config, gepa_enabled, gepa_budget, v3_concurrency,
                   no_escalation, output_prefix):
    """V3: async worker-pool batch run."""
    from .run_async import run_batch_async
    overrides = _build_overrides(category, strategies, n_candidates, skip_retrieval,
                                  models_config, gepa_enabled, gepa_budget, v3_concurrency,
                                  no_escalation, output_prefix)
    cfg = RunConfig.from_yaml(config_path, overrides=overrides)
    out = asyncio.run(run_batch_async(cfg))
    click.echo(f"\nDone. Outputs in: {out}")


@main.command("gepa")
@_add_common
def gepa_cmd(config_path, category, strategies, n_candidates, skip_retrieval,
              models_config, gepa_enabled, gepa_budget, v3_concurrency,
              no_escalation, output_prefix):
    """Revision V2: GEPA-optimize supplementary generator guidance only."""
    from .run_gepa import run_gepa
    overrides = _build_overrides(category, strategies, n_candidates, skip_retrieval,
                                  models_config, True, gepa_budget, v3_concurrency,
                                  no_escalation, output_prefix)
    cfg = RunConfig.from_yaml(config_path, overrides=overrides)
    out = run_gepa(cfg)
    click.echo(f"\nDone. Optimized prompts in: {out}")


@main.command("compact-memory")
@click.option("--runs-root", default="runs", show_default=True)
@click.option("--memory-root", default="memory", show_default=True)
@click.option("--models-config", default="configs/models.yaml", show_default=True)
@click.option("--no-llm", is_flag=True, default=False,
              help="Skip the LLM-written insight; use a deterministic template instead.")
def compact_memory(runs_root: str, memory_root: str, models_config: str, no_llm: bool):
    """V1: walk runs/ and consolidate per-(category, strategy) lessons into memory/."""
    from .memory_compactor import consolidate
    reg = model_registry.load(models_config)
    n = consolidate(runs_root=runs_root, memory_root=memory_root,
                    reflection_model=None if no_llm else reg.orchestrator)
    click.echo(f"appended {n} lessons to memory/category_lessons.jsonl")


@main.command("show-config")
@click.option("--config", "config_path", default="configs/run.yaml", show_default=True)
def show_config(config_path: str) -> None:
    data = yaml.safe_load(Path(config_path).read_text())
    click.echo(yaml.safe_dump(data, sort_keys=False))


@main.command("build-bank")
@click.option("--config", "config_path", default="configs/run.yaml", show_default=True)
@click.option("--quota-per-cell", default=None, type=int, help="Override certified pairs per category×strategy cell.")
@click.option("--max-attempts-per-cell", default=None, type=int)
@click.option("--bank-id", default=None, help="Stable id; reuse to resume an interrupted bank build.")
def build_bank_cmd(config_path: str, quota_per_cell: int | None, max_attempts_per_cell: int | None, bank_id: str | None):
    """Revision V2: generate + dual-audit a frozen bank. No target calls."""
    from .probe_bank import build_probe_bank
    cfg = RunConfig.from_yaml(config_path)
    out = build_probe_bank(
        cfg, quota_per_cell=quota_per_cell,
        max_attempts_per_cell=max_attempts_per_cell, bank_id=bank_id,
    )
    click.echo(f"\nDone. Frozen probe bank: {out}")


@main.command("run-bank")
@click.argument("bank_dir")
@click.option("--config", "config_path", default="configs/run.yaml", show_default=True)
@click.option("--run-id", default=None, help="Stable run id; REUSE the same id to resume safely.")
@click.option("--limit-pairs", default=None, type=click.IntRange(min=1),
              help="Smoke-test only the first N frozen pairs. Omit for the full bank.")
@click.option("--models", default=None,
              help="Optional comma-separated target model IDs. Omit to use configs/models.yaml.")
def run_bank_cmd(bank_dir: str, config_path: str, run_id: str | None,
                 limit_pairs: int | None, models: str | None):
    """Revision V2: run targets over one immutable frozen bank; safely resumable."""
    from .run_bank import run_frozen_bank
    cfg = RunConfig.from_yaml(config_path)
    model_list = [x.strip() for x in models.split(",") if x.strip()] if models else None
    out = asyncio.run(run_frozen_bank(
        cfg, bank_dir, run_id=run_id, limit_pairs=limit_pairs, target_models=model_list
    ))
    click.echo(f"\nDone. Target sweep outputs: {out}")


if __name__ == "__main__":
    main()
