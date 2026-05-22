#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

if [[ $# -gt 0 ]]; then
  shift
fi

LOCK_FILE="${BD_FBUY_ACCUM_PRE_LOCK_FILE:-$PROJECT_DIR/tmp/run_bd_fbuy_accum_pre.lock}"
LOG_FILE="${BD_FBUY_ACCUM_PRE_LOG_FILE:-$PROJECT_DIR/logs/bd_fbuy_accum_pre_intraday_cron.log}"
LIVE_INTRADAY="${BD_FBUY_ACCUM_PRE_LIVE_INTRADAY:-0}"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] bd_fbuy_accum_pre already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.bd_fbuy_accum_pre_scanner --date "$TARGET_DATE" "$@")
if [[ "$LIVE_INTRADAY" == "1" ]]; then
  cmd+=(--live-intraday)
fi

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] bd_fbuy_accum_pre target_date=${TARGET_DATE} started_at=${started_at} live_intraday=${LIVE_INTRADAY}" | tee -a "$LOG_FILE"

if "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[DONE] bd_fbuy_accum_pre target_date=${TARGET_DATE} finished_at=${finished_at}" | tee -a "$LOG_FILE"
else
  exit_code=$?
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[FAIL] bd_fbuy_accum_pre target_date=${TARGET_DATE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi
