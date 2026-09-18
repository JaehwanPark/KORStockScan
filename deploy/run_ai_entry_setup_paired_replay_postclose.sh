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
# Same source-day inputs; no global-DONE predecessor cycle or unrelated legacy
# selector/holding research. Source exclusions are terminal dispositions.
"$VENV_PY" -m src.engine.scalping.entry_setup_paired_replay_batch \
  --date "$TARGET_DATE" --compact-only --execute-compact-candidate \
  --max-new-requests-per-cohort "$MAX_NEW_PER_COHORT" --write --finalize-compact
"$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain \
  --date "$TARGET_DATE" --compact-summary-only --require-summary-handoff
