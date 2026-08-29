#!/usr/bin/env bash
# Revision V2 staged launcher.
# Deliberately requires an explicit phase so generation and target evaluation
# cannot accidentally be mixed.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

phase="${1:-}"
bank_id="${BANK_ID:-revision_v2_bank}"
pilot_id="${PILOT_BANK_ID:-revision_v2_pilot}"

case "$phase" in
  gepa)
    bash scripts/probe_models.sh
    # Writes an optimization_manifest.json proving target/judge signals were absent.
    uv run jbh gepa --config configs/run.yaml --skip-retrieval --no-escalation
    ;;
  pilot)
    # Cheap pre-main-run bank: 5 per cell = 60 total pairs.
    # DeepSeek audits every candidate; GPT-5 Mini only audits DeepSeek passes.
    uv run jbh build-bank --config configs/run.yaml \
      --quota-per-cell 5 --bank-id "$pilot_id"
    ;;
  bank)
    # Full core bank: 4 categories × 3 strategies × 42 = 504 frozen pairs.
    uv run jbh build-bank --config configs/run.yaml \
      --quota-per-cell 42 --bank-id "$bank_id"
    ;;
  targets)
    bank_dir="probe_banks/$bank_id"
    if [ ! -f "$bank_dir/manifest.json" ]; then
      echo "ERROR: frozen bank not found: $bank_dir" >&2
      exit 2
    fi
    uv run jbh run-bank "$bank_dir" --config configs/run.yaml
    ;;
  *)
    echo "Usage: bash scripts/run_revision_v2.sh <gepa|pilot|bank|targets>"
    echo "Optional: BANK_ID=... PILOT_BANK_ID=..."
    exit 2
    ;;
esac
