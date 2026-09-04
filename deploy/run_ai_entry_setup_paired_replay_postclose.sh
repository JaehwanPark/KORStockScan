#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
MAX_NEW_PER_COHORT="${AI_ENTRY_SETUP_REPLAY_MAX_NEW_PER_COHORT:-30}"
CANDIDATE_WORKERS="${AI_ENTRY_SETUP_REPLAY_WORKERS:-2}"
PREDECESSOR_WAIT_SEC="${AI_ENTRY_SETUP_REPLAY_PREDECESSOR_WAIT_SEC:-43200}"
MAX_ATTEMPTS="${AI_ENTRY_SETUP_REPLAY_MAX_ATTEMPTS:-3}"
LOCK_PATH="$PROJECT_DIR/tmp/ai_entry_setup_paired_replay_${TARGET_DATE}.lock"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

exec 9>"$LOCK_PATH"
if ! flock -n 9; then
  echo "[SKIP] ai entry setup replay already running target_date=$TARGET_DATE"
  exit 0
fi

if ! [[ "$MAX_ATTEMPTS" =~ ^[1-9][0-9]*$ ]]; then
  echo "[ERROR] AI_ENTRY_SETUP_REPLAY_MAX_ATTEMPTS must be a positive integer"
  exit 2
fi

run_entry_batch() {
  nice -n 10 ionice -c 2 -n 7 -t \
    "$VENV_PY" -m src.engine.scalping.entry_setup_paired_replay_batch \
    --date "$TARGET_DATE" \
    --max-new-requests-per-cohort "$MAX_NEW_PER_COHORT" \
    --candidate-workers "$CANDIDATE_WORKERS" \
    --predecessor-wait-sec "$PREDECESSOR_WAIT_SEC" \
    --write
}

refresh_main_ai_consumer() {
  # The optimizer consumes the first batch's new results. Re-publish the batch
  # from its checkpoint so its selection-source hash binds that refreshed
  # optimizer generation before the exact-hash consumer validates the chain.
  nice -n 10 ionice -c 2 -n 7 -t \
    "$VENV_PY" -m src.engine.scalping.micro_reversion.main_ai_prompt_optimizer \
    --target-date "$TARGET_DATE" \
    --write \
    --print-summary && \
  run_entry_batch && \
  nice -n 10 ionice -c 2 -n 7 -t \
    "$VENV_PY" -m src.engine.scalping.main_ai_holding_base_replay_batch \
    --date "$TARGET_DATE" \
    --write \
    --print-summary && \
  nice -n 10 ionice -c 2 -n 7 -t \
    "$VENV_PY" -m src.engine.scalping.main_ai_prompt_consumer \
    --target-date "$TARGET_DATE" \
    --write \
    --require-entry-terminal \
    --print-summary
}

for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1)); do
  batch_rc=0
  failure_stage="entry_batch"
  if run_entry_batch; then
    if refresh_main_ai_consumer; then
      exit 0
    else
      batch_rc=$?
      failure_stage="consumer_refresh"
      echo "[WARN] main AI source-only consumer refresh failed attempt=$attempt"
    fi
  else
    batch_rc=$?
  fi
  if [ "$failure_stage" = "entry_batch" ] && [ "$batch_rc" -eq 3 ]; then
    echo "[ERROR] offline candidate batch predecessor bounded wait exhausted target_date=$TARGET_DATE"
    exit 1
  fi
  if ((attempt < MAX_ATTEMPTS)); then
    echo "[WARN] offline candidate batch failed; retrying valid-result checkpoint attempt=$attempt"
    sleep 15
  fi
done

echo "[ERROR] offline candidate batch exhausted attempts=$MAX_ATTEMPTS"
exit 1
