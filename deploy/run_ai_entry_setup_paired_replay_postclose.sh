#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
MAX_NEW_PER_COHORT="${AI_ENTRY_SETUP_REPLAY_MAX_NEW_PER_COHORT:-30}"
mkdir -p "$PROJECT_DIR/tmp"
cd "$PROJECT_DIR"
exec 9>"$PROJECT_DIR/tmp/ai_entry_setup_paired_replay_${TARGET_DATE}.lock"
if ! flock -n 9; then
  echo "[SKIP] compact paired replay already running target_date=$TARGET_DATE"
  exit 0
fi
# One fingerprinted evaluator owns candidate execution and provider-free
# finalization. Source/model gaps stop before a candidate provider call.
"$VENV_PY" -m src.engine.scalping.entry_setup_paired_replay_batch \
  --date "$TARGET_DATE" --data-root "$PROJECT_DIR/data" --compact-only \
  --execute-compact-candidate --finalize-compact \
  --max-new-requests-per-cohort "$MAX_NEW_PER_COHORT" --write
"$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain \
  --date "$TARGET_DATE" --compact-summary-only
