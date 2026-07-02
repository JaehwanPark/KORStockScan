#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

if [[ $# -gt 0 ]]; then
  shift
fi

LOCK_FILE="${RISING_MISSED_INTRADAY_FEEDBACK_LOCK_FILE:-$PROJECT_DIR/tmp/run_rising_missed_intraday_feedback.lock}"
COOLDOWN_STATE_FILE="${RISING_MISSED_INTRADAY_FEEDBACK_COOLDOWN_STATE_FILE:-$PROJECT_DIR/tmp/run_rising_missed_intraday_feedback_success.state}"
COOLDOWN_SEC="${RISING_MISSED_INTRADAY_FEEDBACK_COOLDOWN_SEC:-300}"
LOG_FILE="${RISING_MISSED_INTRADAY_FEEDBACK_LOG_FILE:-$PROJECT_DIR/logs/run_rising_missed_intraday_feedback.log}"
IONICE_CLASS="${RISING_MISSED_INTRADAY_FEEDBACK_IONICE_CLASS:-2}"
IONICE_LEVEL="${RISING_MISSED_INTRADAY_FEEDBACK_IONICE_LEVEL:-7}"
NICE_LEVEL="${RISING_MISSED_INTRADAY_FEEDBACK_NICE_LEVEL:-12}"
NICE_COMMAND="${RISING_MISSED_INTRADAY_FEEDBACK_NICE_COMMAND:-nice}"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

validate_int() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

COOLDOWN_SEC="$(validate_int "$COOLDOWN_SEC" 300)"
IONICE_CLASS="$(validate_int "$IONICE_CLASS" 2)"
IONICE_LEVEL="$(validate_int "$IONICE_LEVEL" 7)"
NICE_LEVEL="$(validate_int "$NICE_LEVEL" 12)"

if [[ -f "$COOLDOWN_STATE_FILE" && "$COOLDOWN_SEC" -gt 0 ]]; then
  last_ts="$(date -r "$COOLDOWN_STATE_FILE" +%s 2>/dev/null || echo 0)"
  now_ts="$(date +%s)"
  elapsed=$((now_ts - last_ts))
  if [[ "$last_ts" -gt 0 && "$elapsed" -lt "$COOLDOWN_SEC" ]]; then
    remaining=$((COOLDOWN_SEC - elapsed))
    echo "[SKIP] rising missed intraday feedback cooldown active remaining=${remaining}s target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    exit 0
  fi
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] rising missed intraday feedback already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.rising_missed_intraday_feedback --target-date "$TARGET_DATE" --print-summary "$@")

if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
  cmd=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t "${cmd[@]}")
fi

if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
  cmd=("$NICE_COMMAND" -n "$NICE_LEVEL" "${cmd[@]}")
fi

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] rising missed intraday feedback target_date=${TARGET_DATE} started_at=${started_at}" | tee -a "$LOG_FILE"

if "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  touch "$COOLDOWN_STATE_FILE"
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[DONE] rising missed intraday feedback target_date=${TARGET_DATE} finished_at=${finished_at}" | tee -a "$LOG_FILE"
else
  exit_code=$?
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[FAIL] rising missed intraday feedback target_date=${TARGET_DATE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi
