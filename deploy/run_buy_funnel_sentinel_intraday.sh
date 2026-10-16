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

LOCK_FILE="${BUY_FUNNEL_SENTINEL_LOCK_FILE:-$PROJECT_DIR/tmp/run_buy_funnel_sentinel.lock}"
COOLDOWN_STATE_FILE="${BUY_FUNNEL_SENTINEL_COOLDOWN_STATE_FILE:-$PROJECT_DIR/tmp/run_buy_funnel_sentinel_success.state}"
# Cron already runs every five minutes and flock prevents overlapping writers.
# A post-completion cooldown skips the next tick and can exceed the ten-minute
# freshness contract even after a successful run. Explicit overrides remain.
COOLDOWN_SEC="${BUY_FUNNEL_SENTINEL_COOLDOWN_SEC:-0}"
LOG_FILE="${BUY_FUNNEL_SENTINEL_LOG_FILE:-$PROJECT_DIR/logs/run_buy_funnel_sentinel.log}"

bash "$SCRIPT_DIR/run_owned_log_rotation.sh" "run_buy_funnel_sentinel_intraday" "$LOG_FILE" || \
  echo "[OWNED_LOG_ROTATION_WARNING] internal rollover failed; work continues" >&2

DRY_RUN="${BUY_FUNNEL_SENTINEL_DRY_RUN:-0}"
USE_CACHE="${BUY_FUNNEL_SENTINEL_USE_CACHE:-1}"
USE_SUMMARY="${BUY_FUNNEL_SENTINEL_USE_SUMMARY:-1}"
IONICE_CLASS="${BUY_FUNNEL_SENTINEL_IONICE_CLASS:-2}"
IONICE_LEVEL="${BUY_FUNNEL_SENTINEL_IONICE_LEVEL:-7}"
NICE_LEVEL="${BUY_FUNNEL_SENTINEL_NICE_LEVEL:-12}"
NICE_COMMAND="${BUY_FUNNEL_SENTINEL_NICE_COMMAND:-nice}"
CPU_AFFINITY="${BUY_FUNNEL_SENTINEL_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity sentinel)}"

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

COOLDOWN_SEC="$(validate_int "$COOLDOWN_SEC" 0)"
IONICE_CLASS="$(validate_int "$IONICE_CLASS" 2)"
IONICE_LEVEL="$(validate_int "$IONICE_LEVEL" 7)"
NICE_LEVEL="$(validate_int "$NICE_LEVEL" 12)"

if [[ -f "$COOLDOWN_STATE_FILE" && "$COOLDOWN_SEC" -gt 0 ]]; then
  last_ts="$(date -r "$COOLDOWN_STATE_FILE" +%s 2>/dev/null || echo 0)"
  now_ts="$(date +%s)"
  elapsed=$((now_ts - last_ts))
  if [[ "$last_ts" -gt 0 && "$elapsed" -lt "$COOLDOWN_SEC" ]]; then
    remaining=$((COOLDOWN_SEC - elapsed))
    echo "[SKIP] buy funnel sentinel cooldown active remaining=${remaining}s target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    exit 0
  fi
fi

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] buy funnel sentinel already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.buy_funnel_sentinel --date "$TARGET_DATE" --print-json "$@")
if [[ "$DRY_RUN" == "1" ]]; then
  cmd+=(--dry-run)
fi
if [[ "$USE_CACHE" == "1" ]]; then
  cmd+=(--use-cache)
fi
if [[ "$USE_SUMMARY" == "1" ]]; then
  cmd+=(--use-summary)
fi

priority=()
if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
  priority+=(taskset -c "$CPU_AFFINITY")
fi
if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
  priority+=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t)
fi
if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
  priority+=("$NICE_COMMAND" -n "$NICE_LEVEL")
fi
# One budget for Sentinel, fallback, observer and owned-child cleanup.
run_started_seconds=$SECONDS
run_bounded() {
  local remaining=$((180 - SECONDS + run_started_seconds - 5))
  [[ "$remaining" -gt 0 ]] || return 75
  timeout --signal=TERM --kill-after=5s "${remaining}s" "${priority[@]}" "$@"
}
run_sentinel() {
  # Keep 40 seconds for the observer and five for this child's TERM grace.
  # The final five-second cleanup reserve and shared 180-second limit remain.
  local remaining=$((180 - SECONDS + run_started_seconds - 5 - 40 - 5))
  [[ "$remaining" -gt 0 ]] || return 75
  timeout --signal=TERM --kill-after=5s "${remaining}s" "${priority[@]}" "$@"
}
run_monitor() {
  local remaining=$((180 - SECONDS + run_started_seconds - 5))
  [[ "$remaining" -ge 20 ]] || return 75
  [[ "$remaining" -le 120 ]] || remaining=120
  run_bounded env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.submission_bottleneck_monitor \
    --report "$PROJECT_DIR/data/report/buy_funnel_sentinel/submission_bottleneck_source_${TARGET_DATE}.json" \
    --notify --reuse-validation-digests --budget-seconds "$remaining" "$@"
}

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] buy funnel sentinel target_date=${TARGET_DATE} started_at=${started_at} dry_run=${DRY_RUN} use_cache=${USE_CACHE} use_summary=${USE_SUMMARY}" | tee -a "$LOG_FILE"

if run_sentinel "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  if [[ "$DRY_RUN" != "1" ]]; then
    if run_monitor 2>&1 | tee -a "$LOG_FILE"; then
      :
    else
      exit_code=$?
      if [[ "$exit_code" -eq 75 ]]; then
        echo "[DEFERRED] buy funnel sentinel target_date=${TARGET_DATE} reason=monitor_deferred exit_code=${exit_code}" | tee -a "$LOG_FILE"
        exit "$exit_code"
      fi
      echo "[FAIL] buy funnel sentinel target_date=${TARGET_DATE} reason=monitor_incomplete exit_code=${exit_code}" | tee -a "$LOG_FILE"
      exit "$exit_code"
    fi
  fi
  touch "$COOLDOWN_STATE_FILE"
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[DONE] buy funnel sentinel target_date=${TARGET_DATE} finished_at=${finished_at} execution_status=completed semantic_status=see_monitor_terminal" | tee -a "$LOG_FILE"
else
  exit_code=$?
  # The source-gap observer reads its own current-day bounded raw receipts.
  # Sentinel failure makes its funnel evidence unobservable, not its independent
  # probe/trace/pending receipts.
  if [[ "$DRY_RUN" != "1" ]]; then
    if ! run_monitor --source-only 2>&1 | tee -a "$LOG_FILE"; then
      echo "[WARN] source-gap observer also failed target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
    fi
  fi
  finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
  echo "[FAIL] buy funnel sentinel target_date=${TARGET_DATE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi
