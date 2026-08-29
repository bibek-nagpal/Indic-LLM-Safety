"""Shared building blocks used by both V1 (sync) and V3 (async) runners.

Keeping these in one place ensures the two runners produce the same
trace records and apply the same niche-escalation behaviour.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Optional

from . import (
    category_spec,
    equivalence,
    evidence_gate,
    flip_detector,
    generator,
    judge,
    memory as mem_mod,
    model_registry,
    model_runner,
    niche_escalator,
    retrieval_exa,
    trace_store,
)


@dataclass
class CandidateWithEq:
    cand: generator.Candidate
    eq: equivalence.EquivalenceReport


def retrieve_and_gate(spec: category_spec.CategorySpec,
                      *, query: str,
                      n_sources: int,
                      reg: model_registry.ModelRegistry,
                      relevance_threshold: float,
                      memory: mem_mod.Memory,
                      ) -> tuple[list[evidence_gate.GatedSource],
                                  list[evidence_gate.GatedSource]]:
    r = retrieval_exa.search(query, num_results=n_sources)
    gated = evidence_gate.gate(
        r.sources, spec,
        summarizer_model=reg.summarizer_model,
        relevance_threshold=relevance_threshold,
        max_tokens=reg.max_orchestrator_tokens,
    )
    for gs in gated.accepted:
        memory.append("retrieval_sources", {
            "category": spec.id, "src_id": gs.source.id, "url": gs.source.url,
            "title": gs.source.title, "relevance_score": gs.relevance_score,
            "summary": gs.neutral_summary, "query": query,
        })
    return gated.accepted, gated.rejected


def generate_and_check(spec: category_spec.CategorySpec,
                        strategy: str,
                        evidence: list[evidence_gate.GatedSource],
                        *,
                        reg: model_registry.ModelRegistry,
                        n: int,
                        memory_context: str,
                        system_override: Optional[str],
                        equivalence_threshold: float,
                        store: trace_store.TraceStore,
                        memory: mem_mod.Memory,
                        ) -> list[CandidateWithEq]:
    try:
        cands = generator.generate(
            spec, strategy, evidence,
            generator_model=reg.generator_model,
            seed_examples=spec.seed_examples,
            n=n,
            memory_context=memory_context,
            temperature=reg.generator_temperature,
            max_tokens=reg.max_orchestrator_tokens,
            system_prompt_override=system_override,
        )
    except Exception as exc:  # noqa: BLE001
        store.append("traces.jsonl",
                      {"event": "generator_failed", "strategy": strategy,
                       "error": str(exc)})
        return []

    accepted: list[CandidateWithEq] = []
    for cand in cands:
        try:
            eq = equivalence.check(
                cand, checker_model=reg.equivalence_model,
                accept_threshold=equivalence_threshold,
                max_tokens=reg.max_orchestrator_tokens,
            )
        except Exception as exc:  # noqa: BLE001
            store.append("traces.jsonl",
                          {"event": "equivalence_failed", "error": str(exc),
                           "candidate": dataclasses.asdict(cand)})
            continue

        store.append("traces.jsonl", {
            "event": "candidate",
            "candidate": dataclasses.asdict(cand),
            "equivalence": dataclasses.asdict(eq),
        })
        if not eq.accepted:
            memory.append("failed_mutations", {
                "category": spec.id, "strategy": strategy,
                "reason": eq.verdict_reason, "equivalence_score": eq.score,
            })
            continue

        accepted.append(CandidateWithEq(cand=cand, eq=eq))
        store.append("candidates_redacted.jsonl", {
            "category": cand.category, "strategy": cand.strategy,
            "scenario": cand.scenario, "target_group": cand.target_group,
            "info_level_requested": cand.info_level_requested,
            "equivalence_score": eq.score, "source_ids": cand.source_ids,
            "requires_human_review": True,
        })
    return accepted


def fire_target_and_judge(cand: generator.Candidate,
                           model: str,
                           *,
                           reg: model_registry.ModelRegistry,
                           store: trace_store.TraceStore,
                           memory: mem_mod.Memory,
                           gate_questions: dict[str, str] | None = None,
                           ) -> Optional[flip_detector.FlipRecord]:
    pair = model_runner.run_pair(
        model, cand.english_prompt, cand.romanized_hindi_prompt,
        max_tokens=reg.max_target_tokens, temperature=reg.target_temperature,
    )
    store.append("traces.jsonl", {
        "event": "model_pair", "model": model,
        "category": cand.category, "strategy": cand.strategy,
        "english": dataclasses.asdict(pair.english),
        "romanized_hindi": dataclasses.asdict(pair.romanized_hindi),
    })
    if pair.english.error or pair.romanized_hindi.error:
        return None

    en_jr = judge.score_response(
        cand.category, cand.english_prompt, pair.english.content,
        judge_model=reg.judge_model, language="en",
        max_tokens=reg.max_judge_tokens,
        gate_questions=gate_questions,
    )
    rh_jr = judge.score_response(
        cand.category, cand.romanized_hindi_prompt,
        pair.romanized_hindi.content,
        judge_model=reg.judge_model, language="rh",
        max_tokens=reg.max_judge_tokens,
        gate_questions=gate_questions,
    )
    for jr, lang in [(en_jr, "en"), (rh_jr, "rh")]:
        store.append("scores.jsonl", {
            "model": model, "language": lang, "category": cand.category,
            "strategy": cand.strategy, "score": jr.score,
            "gate_a": jr.gate_a, "gate_b": jr.gate_b, "gate_c": jr.gate_c,
            "logical_consistency_ok": jr.logical_consistency_ok,
            "looks_like_refusal_regex": jr.looks_like_refusal,
            "response_garbled": jr.response_garbled,
            "rationale": jr.rationale, "framing_used": jr.framing_used,
            "disclaimers_present": jr.disclaimers_present,
            "judge_model": jr.judge_model,
        })
        if not jr.logical_consistency_ok:
            memory.append("judge_disagreements", {
                "category": cand.category, "strategy": cand.strategy,
                "model": model, "language": lang, "score": jr.score,
                "gates": [jr.gate_a, jr.gate_b, jr.gate_c],
                "rationale": jr.rationale,
            })

    flip = flip_detector.detect(
        category=cand.category, strategy=cand.strategy, model=model,
        en_result=en_jr, rh_result=rh_jr,
    )
    store.append("flips.jsonl", flip)
    if flip.flip or flip.critical_flip:
        memory.append("successful_patterns_redacted",
                       mem_mod.redacted_pattern_record(
            category=cand.category, strategy=cand.strategy, model=model,
            en_score=flip.en_score, rh_score=flip.rh_score,
            flip=flip.flip, critical_flip=flip.critical_flip,
            equivalence_score=0.0,
            judge_rationale_summary=(
                f"en: {en_jr.rationale[:200]} | rh: {rh_jr.rationale[:200]}"
            ),
        ))
    return flip


def gather_niche_evidence(spec,
                           *, reg: model_registry.ModelRegistry,
                           memory: mem_mod.Memory,
                           store: trace_store.TraceStore,
                           max_queries: int,
                           relevance_threshold: float,
                           sources_per_query: int = 2,
                           ) -> list[evidence_gate.GatedSource]:
    """Run the niche-escalator -> Exa -> EvidenceGate path. Returns
    accepted niche sources to feed into a re-generation round.

    Accepts CategorySpec or CategoryBundle. In bundle mode, we pull
    failed_mutations across ALL member categories and use a synthetic
    'multi' key for the expander."""
    failed = memory.tail("failed_mutations", n=40)
    if hasattr(spec, "members"):
        member_ids = {s.id for s in spec.members}
        failed = [f for f in failed if f.get("category") in member_ids]
        # In bundle mode, gather niche queries for EACH member then merge.
        all_queries: list[str] = []
        all_fallback = True
        for member in spec.members:
            exp = niche_escalator.expanded_queries(
                member.id,
                [f for f in failed if f.get("category") == member.id],
                orchestrator_model=reg.orchestrator,
                n=max(1, max_queries // max(1, len(spec.members))),
                max_tokens=reg.max_orchestrator_tokens,
            )
            all_queries.extend(exp.queries)
            all_fallback = all_fallback and exp.fallback_used
        exp = niche_escalator.ExpandedQueries(
            queries=all_queries[:max_queries], fallback_used=all_fallback,
        )
    else:
        exp = niche_escalator.expanded_queries(
            spec.id, [f for f in failed if f.get("category") == spec.id],
            orchestrator_model=reg.orchestrator,
            n=max_queries, max_tokens=reg.max_orchestrator_tokens,
        )
    store.append("traces.jsonl", {
        "event": "niche_queries", "category": spec.id,
        "fallback_used": exp.fallback_used,
        "queries": exp.queries[: max_queries],
    })
    accepted_all: list[evidence_gate.GatedSource] = []
    for q in exp.queries[:max_queries]:
        try:
            accepted, _ = retrieve_and_gate(
                spec, query=q, n_sources=sources_per_query, reg=reg,
                relevance_threshold=relevance_threshold, memory=memory,
            )
            accepted_all.extend(accepted)
        except Exception as exc:  # noqa: BLE001
            store.append("traces.jsonl",
                          {"event": "niche_retrieval_failed", "query": q,
                           "error": str(exc)})
    return accepted_all
