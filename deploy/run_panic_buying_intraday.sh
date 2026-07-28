#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"

if [[ $# -gt 0 ]]; then
  shift
fi

LOCK_FILE="${PANIC_BUYING_LOCK_FILE:-$PROJECT_DIR/tmp/run_panic_buying.lock}"
COOLDOWN_STATE_FILE="${PANIC_BUYING_COOLDOWN_STATE_FILE:-$PROJECT_DIR/tmp/run_panic_buying_success.state}"
COOLDOWN_SEC="${PANIC_BUYING_COOLDOWN_SEC:-90}"
LOG_FILE="${PANIC_BUYING_LOG_FILE:-$PROJECT_DIR/logs/run_panic_buying.log}"
DRY_RUN="${PANIC_BUYING_DRY_RUN:-0}"
NOTIFY_ENABLED="${PANIC_BUYING_NOTIFY_TELEGRAM_ENABLED:-true}"
NOTIFY_AUDIENCE="${PANIC_BUYING_NOTIFY_AUDIENCE:-all}"
NOTIFY_STATE_FILE="${PANIC_BUYING_NOTIFY_STATE_FILE:-$PROJECT_DIR/tmp/panic_state_telegram_notify_state.json}"
MARKET_BREADTH_COLLECT_ENABLED="${PANIC_MARKET_BREADTH_COLLECT_ENABLED:-true}"
MARKET_BREADTH_MAX_AGE_SEC="${PANIC_MARKET_BREADTH_MAX_AGE_SEC:-75}"
MARKET_BREADTH_LOCK_FILE="${PANIC_MARKET_BREADTH_LOCK_FILE:-$PROJECT_DIR/tmp/run_market_panic_breadth.lock}"
IONICE_CLASS="${PANIC_BUYING_IONICE_CLASS:-2}"
IONICE_LEVEL="${PANIC_BUYING_IONICE_LEVEL:-7}"
NICE_LEVEL="${PANIC_BUYING_NICE_LEVEL:-12}"
NICE_COMMAND="${PANIC_BUYING_NICE_COMMAND:-nice}"
CPU_AFFINITY="${PANIC_BUYING_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity panic)}"
OPERATOR_OVERRIDE_ENABLED="${KORSTOCKSCAN_PANIC_BUYING_REPORT_OPERATOR_OVERRIDE:-false}"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

case "${OPERATOR_OVERRIDE_ENABLED,,}" in
  1|true|yes|on) ;;
  *)
    echo "[DISABLED] panic buying report is permanently stopped; explicit operator override required target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    exit 0
    ;;
esac

validate_int() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

COOLDOWN_SEC="$(validate_int "$COOLDOWN_SEC" 90)"
MARKET_BREADTH_MAX_AGE_SEC="$(validate_int "$MARKET_BREADTH_MAX_AGE_SEC" 75)"
IONICE_CLASS="$(validate_int "$IONICE_CLASS" 2)"
IONICE_LEVEL="$(validate_int "$IONICE_LEVEL" 7)"
NICE_LEVEL="$(validate_int "$NICE_LEVEL" 12)"

market_breadth_fresh() {
  local report_file="$PROJECT_DIR/data/report/market_panic_breadth/market_panic_breadth_${TARGET_DATE}.json"
  if [[ ! -f "$report_file" || "$MARKET_BREADTH_MAX_AGE_SEC" -le 0 ]]; then
    return 1
  fi
  local last_ts now_ts age
  last_ts="$(date -r "$report_file" +%s 2>/dev/null || echo 0)"
  now_ts="$(date +%s)"
  age=$((now_ts - last_ts))
  [[ "$last_ts" -gt 0 && "$age" -le "$MARKET_BREADTH_MAX_AGE_SEC" ]]
}

run_market_breadth_collect() {
  local report_file="$PROJECT_DIR/data/report/market_panic_breadth/market_panic_breadth_${TARGET_DATE}.json"
  if market_breadth_fresh; then
    echo "[SKIP] market panic breadth fresh target_date=${TARGET_DATE} max_age_sec=${MARKET_BREADTH_MAX_AGE_SEC} path=${report_file}" | tee -a "$LOG_FILE"
    return 0
  fi

  exec 8>"$MARKET_BREADTH_LOCK_FILE"
  if ! flock -n 8; then
    echo "[WAIT] market panic breadth already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    local waited=0
    while [[ "$waited" -lt "$MARKET_BREADTH_MAX_AGE_SEC" ]]; do
      sleep 5
      waited=$((waited + 5))
      if market_breadth_fresh; then
        echo "[SKIP] market panic breadth reused after wait=${waited}s target_date=${TARGET_DATE} path=${report_file}" | tee -a "$LOG_FILE"
        return 0
      fi
    done
    echo "[WARN] market panic breadth lock wait timeout target_date=${TARGET_DATE}; continuing panic report with prior/missing breadth" | tee -a "$LOG_FILE"
    return 0
  fi

  if market_breadth_fresh; then
    echo "[SKIP] market panic breadth fresh after lock target_date=${TARGET_DATE} max_age_sec=${MARKET_BREADTH_MAX_AGE_SEC} path=${report_file}" | tee -a "$LOG_FILE"
    return 0
  fi

  local breadth_cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.market_panic_breadth_collector --date "$TARGET_DATE" --print-json)
  if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
    breadth_cmd=(taskset -c "$CPU_AFFINITY" "${breadth_cmd[@]}")
  fi
  if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
    breadth_cmd=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t "${breadth_cmd[@]}")
  fi
  if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
    breadth_cmd=("$NICE_COMMAND" -n "$NICE_LEVEL" "${breadth_cmd[@]}")
  fi

  echo "[START] market panic breadth collect target_date=${TARGET_DATE} affinity=${CPU_AFFINITY} max_age_sec=${MARKET_BREADTH_MAX_AGE_SEC}" | tee -a "$LOG_FILE"
  if "${breadth_cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
    echo "[DONE] market panic breadth collect target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  else
    echo "[WARN] market panic breadth collect failed target_date=${TARGET_DATE}; continuing panic report with prior/missing breadth" | tee -a "$LOG_FILE"
  fi
}

if [[ -f "$COOLDOWN_STATE_FILE" && "$COOLDOWN_SEC" -gt 0 ]]; then
  last_ts="$(date -r "$COOLDOWN_STATE_FILE" +%s 2>/dev/null || echo 0)"
  now_ts="$(date +%s)"
  elapsed=$((now_ts - last_ts))
  if [[ "$last_ts" -gt 0 && "$elapsed" -lt "$COOLDOWN_SEC" ]]; then
    remaining=$((COOLDOWN_SEC - elapsed))
    echo "[SKIP] panic buying cooldown active remaining=${remaining}s target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    exit 0
  fi
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] panic buying already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.panic_buying_report --date "$TARGET_DATE" --print-json "$@")
if [[ "$DRY_RUN" == "1" ]]; then
  cmd+=(--dry-run)
fi

if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
  cmd=(taskset -c "$CPU_AFFINITY" "${cmd[@]}")
fi

if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
  cmd=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t "${cmd[@]}")
fi

if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
  cmd=("$NICE_COMMAND" -n "$NICE_LEVEL" "${cmd[@]}")
fi

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] panic buying target_date=${TARGET_DATE} started_at=${started_at} dry_run=${DRY_RUN}" | tee -a "$LOG_FILE"

if [[ "$MARKET_BREADTH_COLLECT_ENABLED" != "0" && "$MARKET_BREADTH_COLLECT_ENABLED" != "false" && "$MARKET_BREADTH_COLLECT_ENABLED" != "no" && "$MARKET_BREADTH_COLLECT_ENABLED" != "off" ]]; then
  run_market_breadth_collect
fi

if "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  REPORT_FILE="$PROJECT_DIR/data/report/panic_buying/panic_buying_${TARGET_DATE}.json"
  if [[ "$NOTIFY_ENABLED" != "0" && "$NOTIFY_ENABLED" != "false" && "$NOTIFY_ENABLED" != "no" && "$NOTIFY_ENABLED" != "off" && -f "$REPORT_FILE" ]]; then
    notify_audience="$NOTIFY_AUDIENCE"
    if [[ "$DRY_RUN" == "1" ]]; then
      notify_audience="admin"
    fi
    env PYTHONPATH=. "$VENV_PY" -m src.engine.notify_panic_state_transition \
      --report-file "$REPORT_FILE" \
      --kind panic_buying \
      --audience "$notify_audience" \
      --state-file "$NOTIFY_STATE_FILE" 2>&1 | tee -a "$LOG_FILE" || true
  fi
  touch "$COOLDOWN_STATE_FILE"
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[DONE] panic buying target_date=${TARGET_DATE} finished_at=${finished_at}" | tee -a "$LOG_FILE"
else
  exit_code=$?
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[FAIL] panic buying target_date=${TARGET_DATE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi
