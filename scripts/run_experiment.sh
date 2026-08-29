#!/usr/bin/env bash
# run_experiment.sh — Jailbreak Hermes Experiment 2
#
# 12 batches: 4 categories × 3 target models. Each batch pins ONE target
# model via JBH_TARGET_MODELS and writes its own runs/ directory.
#
# Batches run in PARALLEL (up to MAX_PARALLEL at once); within a batch,
# `v3_concurrency` requests are in flight per stage. The orchestrator,
# judge, generator and equivalence models are PAID with large limits, so
# we run full throttle. The only free-tier model (nemotron) can hit 429s —
# the OpenRouter client rides those out (wait-it-out retry, see
# openrouter_client.py), so a throttled nemotron batch slows only itself,
# never the paid batches.
#
# Effective peak concurrency on the shared orchestrator ≈
#   MAX_PARALLEL × v3_concurrency
# If you see *sustained* 429s on a paid model, lower one of those two.
#
# Cost: ~$3 total across all 12 batches.
#
# Usage:
#   ./scripts/run_experiment.sh                    # all 12 batches, full parallel
#   N_CANDIDATES=50 ./scripts/run_experiment.sh    # override trial count
#   MAX_PARALLEL=4 ./scripts/run_experiment.sh     # cap concurrent batches
#   ./scripts/run_experiment.sh --max-parallel 6   # same, as a flag
#   ./scripts/run_experiment.sh --resume           # skip already-run batches
#   ./scripts/run_experiment.sh --gepa-only        # only run GEPA
#   ./scripts/run_experiment.sh violence           # single category (3 batches)
#   ./scripts/run_experiment.sh --no-probe         # skip pre-flight model probe
#
# Per-batch live logs:  runs/logs/exp2_<category>_<model>_<ts>.log
# Output run dirs:      runs/exp2_<category>_<model>_run_YYYYMMDD_HHMMSS/

set -euo pipefail

# REVISION V2 SAFETY GUARD --------------------------------------------------
# This launcher reproduces the submitted V1 design, where each target received
# independently generated prompts. It is intentionally disabled for the
# revision experiment. Use scripts/run_revision_v2.sh instead.
if [ "${JBH_ALLOW_LEGACY_V1:-0}" != "1" ]; then
    echo "ERROR: scripts/run_experiment.sh is the LEGACY V1 launcher and is disabled."
    echo "Use: bash scripts/run_revision_v2.sh <gepa|pilot|bank|targets>"
    echo "Set JBH_ALLOW_LEGACY_V1=1 only if you explicitly want to reproduce V1."
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
N_CANDIDATES="${N_CANDIDATES:-40}"

# Max concurrent batches. 0 (default) = launch ALL queued batches at once.
MAX_PARALLEL="${MAX_PARALLEL:-0}"
# Small delay between launches so N processes don't hammer GEPA-load / Exa
# at the exact same instant. Set 0 to disable.
LAUNCH_STAGGER="${LAUNCH_STAGGER:-2}"

CATEGORIES=(violence intoxication gambling sexual_violence)

MODELS=(
    "qwen/qwen3-30b-a3b-instruct-2507"
    "openai/gpt-oss-20b"
    "nvidia/nemotron-3-nano-30b-a3b:free"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)] WARN${NC} $*"; }
err()  { echo -e "${RED}[$(date +%H:%M:%S)] ERROR${NC} $*"; }
info() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $*"; }
short_name() { echo "$1" | sed 's|.*/||; s|:.*||; s|-free||'; }
_ts() { date +%s; }

# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------
check_prereqs() {
    if ! command -v uv &>/dev/null; then
        err "uv not installed.  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    if [ ! -f .env ]; then
        err ".env not found.  cp .env.example .env  then fill in keys."
        exit 1
    fi
    if ! grep -qE 'OPENROUTER_API_KEY=sk-' .env 2>/dev/null; then
        if [ -z "${OPENROUTER_API_KEY:-}" ]; then
            err "OPENROUTER_API_KEY not set in .env or environment."
            exit 1
        fi
    fi
    log "Pre-flight OK"
}

# Probe every model in the lineup (orchestrator + targets) for reachability,
# credit (402) and rate-limit (429) BEFORE we launch the parallel storm.
# Aborts only on a PAID model failing; a throttled free model is a warning.
run_probe() {
    log "Probing models before launch (scripts/probe_models.sh)..."
    if ! bash scripts/probe_models.sh; then
        err "Model probe reported a hard failure on a required model. Aborting."
        err "Re-run with --no-probe to skip this check at your own risk."
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Phase 0: GEPA optimization (one-time, before any data collection)
# ---------------------------------------------------------------------------
run_gepa() {
    if ls prompts/optimized/*/generator.txt &>/dev/null 2>&1; then
        local latest
        latest=$(ls -dt prompts/optimized/*/generator.txt 2>/dev/null | head -1)
        info "GEPA output exists: ${latest}"
        info "Delete prompts/optimized/ or use --gepa-only --force to re-optimize."
        return 0
    fi

    log "============================================================"
    log "PHASE 0: GEPA optimization (~80 orchestrator calls)"
    log "============================================================"
    uv run jbh gepa \
        --config configs/run.yaml \
        --gepa-budget 8 \
        --skip-retrieval \
        --no-escalation \
        || { err "GEPA failed"; return 1; }

    local out
    out=$(ls -dt prompts/optimized/*/generator.txt 2>/dev/null | head -1)
    [ -n "$out" ] && log "GEPA saved: ${out}" || warn "No generator.txt found after GEPA"
}

# ---------------------------------------------------------------------------
# Resume check — has this (category, model) batch already produced data?
# ---------------------------------------------------------------------------
batch_already_done() {
    local category="$1" target_model="$2"
    local model_short prefix d
    model_short=$(short_name "$target_model")
    prefix="exp2_${category}_${model_short}"
    d=$(ls -dt "runs/${prefix}_"* 2>/dev/null | head -1)
    [ -n "$d" ] && [ -f "$d/flips.jsonl" ] && [ -s "$d/flips.jsonl" ]
}

# ---------------------------------------------------------------------------
# One batch, in the background. Pins its OWN target model and log file.
# ---------------------------------------------------------------------------
run_batch_bg() {
    local category="$1" target_model="$2" logfile="$3"
    local model_short prefix
    model_short=$(short_name "$target_model")
    prefix="exp2_${category}_${model_short}"
    (
        export JBH_TARGET_MODELS="$target_model"
        uv run jbh run-async \
            --config configs/run.yaml \
            --category "${category}" \
            --strategies "Cls1SMCR,Cls2SN,Cls3LA" \
            --n-candidates "${N_CANDIDATES}" \
            --output-prefix "${prefix}" \
            --no-escalation \
            --gepa-enabled
    ) >"$logfile" 2>&1
}

report_batch() {
    local name="$1" prefix="$2" logfile="$3"
    local d np nf nc
    d=$(ls -dt "runs/${prefix}_"* 2>/dev/null | head -1)
    if [ -n "$d" ] && [ -f "$d/flips.jsonl" ]; then
        np=$(wc -l < "$d/flips.jsonl")
        nf=$(grep -c '"flip": true' "$d/flips.jsonl" 2>/dev/null) || nf=0
        nc=$(grep -c '"critical_flip": true' "$d/flips.jsonl" 2>/dev/null) || nc=0
        info "  DONE ${name}: ${nf} flips (${nc} crit) / ${np} pairs  ->  ${d}"
    else
        warn "  DONE ${name} but no flips.jsonl (check ${logfile})"
    fi
}

# ---------------------------------------------------------------------------
# Parallel scheduler — launches jobs up to MAX_PARALLEL, drains as they finish.
# Args: "category|model" pairs.
# Sets globals: SCHED_FAILED (count), SCHED_FAILED_NAMES (array).
# ---------------------------------------------------------------------------
schedule_jobs() {
    local -a jobs=("$@")
    local -A pid_name pid_prefix pid_log
    local running=0 idx=0 launched=0 n=${#jobs[@]}
    SCHED_FAILED=0
    SCHED_FAILED_NAMES=()

    while [ $idx -lt $n ] || [ $running -gt 0 ]; do
        # Fill up to the cap.
        while [ $idx -lt $n ] && [ $running -lt "$MAX_PARALLEL" ]; do
            local cat="${jobs[$idx]%%|*}" model="${jobs[$idx]#*|}"
            local mshort prefix logfile pid
            mshort=$(short_name "$model")
            prefix="exp2_${cat}_${mshort}"
            logfile="runs/logs/${prefix}_$(date +%Y%m%d_%H%M%S).log"
            launched=$((launched + 1))
            info "[launch ${launched}/${n}] ${cat}/${mshort}  (running=$((running+1))/${MAX_PARALLEL})  -> ${logfile}"
            run_batch_bg "$cat" "$model" "$logfile" &
            pid=$!
            pid_name[$pid]="${cat}/${mshort}"
            pid_prefix[$pid]="$prefix"
            pid_log[$pid]="$logfile"
            running=$((running + 1))
            idx=$((idx + 1))
            [ "$LAUNCH_STAGGER" != "0" ] && sleep "$LAUNCH_STAGGER"
        done

        # Wait for ONE job to finish (set -e safe via the `if` guard).
        if [ $running -gt 0 ]; then
            local finished_pid rc
            if wait -n -p finished_pid; then rc=0; else rc=$?; fi
            running=$((running - 1))
            local name="${pid_name[$finished_pid]:-?}"
            local prefix="${pid_prefix[$finished_pid]:-}"
            local logf="${pid_log[$finished_pid]:-?}"
            if [ "$rc" -eq 0 ]; then
                report_batch "$name" "$prefix" "$logf"
            else
                err "FAILED ${name} (exit=${rc})  see ${logf}"
                SCHED_FAILED=$((SCHED_FAILED + 1))
                SCHED_FAILED_NAMES+=("$name")
            fi
        fi
    done
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    local resume=false gepa_only=false do_probe=true
    local categories=("${CATEGORIES[@]}")

    while [ $# -gt 0 ]; do
        case "$1" in
            --resume)       resume=true; shift ;;
            --gepa-only)    gepa_only=true; shift ;;
            --no-probe)     do_probe=false; shift ;;
            --max-parallel) MAX_PARALLEL="$2"; shift 2 ;;
            violence|intoxication|gambling|sexual_violence)
                            categories=("$1"); shift ;;
            *) warn "ignoring unknown arg: $1"; shift ;;
        esac
    done

    check_prereqs

    local total_batches=$(( ${#categories[@]} * ${#MODELS[@]} ))
    # 0 means "all at once"; also clamp to total.
    if [ "$MAX_PARALLEL" -le 0 ] || [ "$MAX_PARALLEL" -gt "$total_batches" ]; then
        MAX_PARALLEL="$total_batches"
    fi
    local total_candidates=$(( ${#categories[@]} * 3 * N_CANDIDATES ))

    echo ""
    log "Jailbreak Hermes — Experiment 2 (parallel)"
    log "=========================================="
    log "Orchestrator:    google/gemini-2.5-flash  (paid)"
    log "Targets:         ${MODELS[*]}"
    log "Categories:      ${#categories[@]} (${categories[*]})"
    log "Strategies:      Cls1SMCR, Cls2SN, Cls3LA"
    log "Candidates/str:  ${N_CANDIDATES}  (total: ${total_candidates})"
    log "Batches:         ${total_batches}"
    log "Max parallel:    ${MAX_PARALLEL} batches  × v3_concurrency/stage"
    log "Launch stagger:  ${LAUNCH_STAGGER}s"
    log ""
    log "Indian context:  ON (Exa + EvidenceGate)"
    log "Escalation:      OFF    Memory context: OFF    GEPA: ON (pre-optimized)"
    log "Resume:          ${resume}"
    log ""

    [ "$do_probe" = true ] && run_probe

    # ---- Phase 0 ----
    run_gepa || { err "GEPA failed — aborting"; exit 1; }
    $gepa_only && { log "GEPA-only mode. Done."; exit 0; }

    # ---- Build the job queue (honoring --resume) ----
    mkdir -p runs/logs
    local -a queue=()
    local skipped=0
    for cat in "${categories[@]}"; do
        for model_id in "${MODELS[@]}"; do
            if $resume && batch_already_done "$cat" "$model_id"; then
                info "SKIP ${cat}/$(short_name "$model_id") (already done)"
                skipped=$((skipped + 1))
                continue
            fi
            queue+=("${cat}|${model_id}")
        done
    done

    echo ""
    log "============================================================"
    log "PHASE 1: Data collection — ${#queue[@]} batches, ${MAX_PARALLEL}-way parallel"
    log "============================================================"
    log "Tail any batch with:  tail -f runs/logs/<batch>.log"
    echo ""

    local start_ts; start_ts=$(_ts)
    if [ "${#queue[@]}" -gt 0 ]; then
        schedule_jobs "${queue[@]}"
    else
        warn "Nothing to run (all batches already complete?)."
        SCHED_FAILED=0; SCHED_FAILED_NAMES=()
    fi

    local end_ts elapsed mins secs
    end_ts=$(_ts); elapsed=$(( end_ts - start_ts ))
    mins=$(( elapsed / 60 )); secs=$(( elapsed % 60 ))

    echo ""
    log "============================================================"
    log "Experiment 2 complete"
    log "Elapsed: ${mins}m ${secs}s  |  Failed: ${SCHED_FAILED}  |  Skipped: ${skipped}  |  Total: ${total_batches}"
    [ "${SCHED_FAILED}" -gt 0 ] && err "Failed batches: ${SCHED_FAILED_NAMES[*]}"
    log "============================================================"

    echo ""
    info "Run summary (all exp2_* dirs with data):"
    for d in runs/exp2_*/; do
        [ -d "$d" ] || continue
        [ -f "$d/flips.jsonl" ] && [ -s "$d/flips.jsonl" ] || continue
        local np nf nc
        np=$(wc -l < "$d/flips.jsonl")
        nf=$(grep -c '"flip": true' "$d/flips.jsonl" 2>/dev/null) || nf=0
        nc=$(grep -c '"critical_flip": true' "$d/flips.jsonl" 2>/dev/null) || nc=0
        printf "  %-55s  %3s flips (%2s crit) / %3s pairs\n" "$d" "$nf" "$nc" "$np"
    done

    exit "${SCHED_FAILED}"
}

main "$@"
