#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
mkdir -p "$PROJECT_DIR/tmp"
cd "$PROJECT_DIR"
exec 9>"$PROJECT_DIR/tmp/ai_entry_setup_paired_replay_${TARGET_DATE}.lock"
if ! flock -n 9; then
  echo "[SKIP] compact paired replay already running target_date=$TARGET_DATE"
  exit 0
fi
# The main postclose wrapper owns calculation. This follower only verifies it.
exec "$VENV_PY" -m src.engine.automation.postclose_summary_handoff \
  --stage main_auxiliary_policy --date "$TARGET_DATE" --check
