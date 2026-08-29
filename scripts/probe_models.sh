#!/usr/bin/env bash
# Pre-flight probe: hit every model in the Experiment-2 lineup (orchestrator
# + 3 targets) with a harmless prompt and classify the response.
# Run BEFORE starting the experiment.
#
# Exit code:
#   0  — all REQUIRED (paid) models reachable. Free-model 429s are warnings only.
#   1  — a required model failed (4xx/5xx other than 429, network, or timeout).
#
# Usage:  bash scripts/probe_models.sh
set -uo pipefail   # not -e: we want to probe every model and tally results

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
    echo "ERROR: .env not found. Run: cp .env.example .env  then fill in keys."
    exit 1
fi
set -a; source .env; set +a

# model|role  — "required" means a failure aborts the experiment; "free" is best-effort.
LINEUP=(
    "google/gemini-2.5-flash|required (generator/judge/summarizer/GEPA reflection)"
    "deepseek/deepseek-v4-flash|required (primary equivalence auditor)"
    "openai/gpt-5-mini|required (secondary equivalence auditor)"
    "qwen/qwen3-30b-a3b-instruct-2507|required (target)"
    "openai/gpt-oss-20b|required (target)"
    "nvidia/nemotron-3-nano-30b-a3b:free|free (target — 429 OK, will self-throttle)"
)

echo "Probing revision-V2 lineup (harmless test prompt)..."
echo "====================================================="

required_fail=0
for entry in "${LINEUP[@]}"; do
    model="${entry%%|}"; model="${entry%%|*}"
    role="${entry#*|}"
    printf "  %-38s [%s]\n    " "$model" "$role"

    status=$(MODEL="$model" python3 -c "
import os, httpx, time, sys
start = time.time()
try:
    r = httpx.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {os.environ[\"OPENROUTER_API_KEY\"]}',
            'Content-Type': 'application/json',
        },
        json={
            'model': os.environ['MODEL'],
            'messages': [{'role': 'user', 'content': 'Say hello in exactly 3 words.'}],
            'max_tokens': 30,
            'temperature': 0,
        },
        timeout=30,
    )
    elapsed = time.time() - start
    data = r.json()
    if r.status_code == 200 and 'choices' in data:
        content = data['choices'][0]['message'].get('content') or \
                  data['choices'][0]['message'].get('reasoning') or ''
        print(f'OK   ({elapsed:.1f}s): {content.strip()[:70]!r}')
        sys.exit(0)
    if r.status_code == 429:
        print(f'RATELIMIT 429 ({elapsed:.1f}s) — retry path will ride this out')
        sys.exit(2)
    if r.status_code == 402:
        print(f'NO-CREDIT 402 ({elapsed:.1f}s): {str(data)[:120]}')
        sys.exit(1)
    err = data.get('error', {}).get('message', str(data)[:150])
    print(f'FAIL HTTP {r.status_code} ({elapsed:.1f}s): {err}')
    sys.exit(1)
except Exception as e:
    print(f'ERR  : {e}')
    sys.exit(1)
")
    rc=$?
    echo "$status" | sed 's/^/    /'
    if [ "$rc" -eq 1 ] && [[ "$role" == required* ]]; then
        required_fail=$((required_fail + 1))
    fi
done

echo ""
if [ "$required_fail" -gt 0 ]; then
    echo "RESULT: ${required_fail} REQUIRED model(s) failed — do NOT start the experiment."
    exit 1
fi
echo "RESULT: all required models reachable. (Any free-model 429 above will"
echo "        self-throttle via the client's wait-it-out retry.)"
exit 0
