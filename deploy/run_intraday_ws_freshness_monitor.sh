#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

if [[ $# -gt 0 ]]; then
  shift
fi

LOCK_FILE="${INTRADAY_WS_FRESHNESS_MONITOR_LOCK_FILE:-$PROJECT_DIR/tmp/run_intraday_ws_freshness_monitor.lock}"
COOLDOWN_STATE_FILE="${INTRADAY_WS_FRESHNESS_MONITOR_COOLDOWN_STATE_FILE:-$PROJECT_DIR/tmp/run_intraday_ws_freshness_monitor_success.state}"
COOLDOWN_SEC="${INTRADAY_WS_FRESHNESS_MONITOR_COOLDOWN_SEC:-300}"
LOG_FILE="${INTRADAY_WS_FRESHNESS_MONITOR_LOG_FILE:-$PROJECT_DIR/logs/run_intraday_ws_freshness_monitor.log}"
IONICE_CLASS="${INTRADAY_WS_FRESHNESS_MONITOR_IONICE_CLASS:-2}"
IONICE_LEVEL="${INTRADAY_WS_FRESHNESS_MONITOR_IONICE_LEVEL:-7}"
NICE_LEVEL="${INTRADAY_WS_FRESHNESS_MONITOR_NICE_LEVEL:-12}"
NICE_COMMAND="${INTRADAY_WS_FRESHNESS_MONITOR_NICE_COMMAND:-nice}"
MONITOR_ONLY="${INTRADAY_WS_FRESHNESS_MONITOR_ONLY:-true}"

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
    echo "[SKIP] intraday ws freshness monitor cooldown active remaining=${remaining}s target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    exit 0
  fi
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] intraday ws freshness monitor already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.intraday_ws_freshness_monitor --target-date "$TARGET_DATE" --write "$@")
if [[ "$MONITOR_ONLY" == "1" || "$MONITOR_ONLY" == "true" || "$MONITOR_ONLY" == "yes" || "$MONITOR_ONLY" == "on" ]]; then
  cmd+=(--monitor-only)
fi

if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
  cmd=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t "${cmd[@]}")
fi

if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
  cmd=("$NICE_COMMAND" -n "$NICE_LEVEL" "${cmd[@]}")
fi

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] intraday ws freshness monitor target_date=${TARGET_DATE} started_at=${started_at} monitor_only=${MONITOR_ONLY}" | tee -a "$LOG_FILE"

if "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  touch "$COOLDOWN_STATE_FILE"
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[DONE] intraday ws freshness monitor target_date=${TARGET_DATE} finished_at=${finished_at}" | tee -a "$LOG_FILE"
else
  exit_code=$?
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[FAIL] intraday ws freshness monitor target_date=${TARGET_DATE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi
