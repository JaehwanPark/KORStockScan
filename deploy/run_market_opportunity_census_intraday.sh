#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
LOCK_FILE="${MARKET_OPPORTUNITY_CENSUS_LOCK_FILE:-$PROJECT_DIR/tmp/run_market_opportunity_census_intraday.lock}"
LOG_FILE="${MARKET_OPPORTUNITY_CENSUS_LOG_FILE:-$PROJECT_DIR/logs/run_market_opportunity_census_intraday.log}"
REFRESH_REPORT="${MARKET_OPPORTUNITY_CENSUS_REFRESH_REPORT:-auto}"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[SKIP] market opportunity census already running target_date=${TARGET_DATE}" | tee -a "$LOG_FILE"
  exit 0
fi

now_hhmm="$(TZ=Asia/Seoul date +%H%M)"
if (( 10#$now_hhmm >= 800 && 10#$now_hhmm < 900 )); then
  venues="NXT"
elif (( 10#$now_hhmm >= 900 && 10#$now_hhmm <= 1530 )); then
  venues="KRX,NXT"
elif (( 10#$now_hhmm > 1530 && 10#$now_hhmm < 2000 )); then
  venues="NXT"
else
  echo "[SKIP] market opportunity census outside capture window target_date=${TARGET_DATE} hhmm=${now_hhmm}" | tee -a "$LOG_FILE"
  exit 0
fi

if [[ "$REFRESH_REPORT" == "auto" ]]; then
  case "$now_hhmm" in
    0915|1200|1515|1945) REFRESH_REPORT="true" ;;
    *) REFRESH_REPORT="false" ;;
  esac
fi

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] market opportunity census target_date=${TARGET_DATE} venues=${venues} refresh_report=${REFRESH_REPORT} runtime_effect=false started_at=${started_at}" | tee -a "$LOG_FILE"

capture_cmd=(
  env PYTHONPATH=.
  "$VENV_PY" -m src.engine.monitoring.market_opportunity_census
  --target-date "$TARGET_DATE"
  --capture
  --capture-only
  --venues "$venues"
  --panels all,liquid_common
  --limit 200
)

if ! "${capture_cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
  exit_code=${PIPESTATUS[0]}
  finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
  echo "[FAIL] market opportunity census target_date=${TARGET_DATE} phase=capture exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
  exit "$exit_code"
fi

if [[ "$REFRESH_REPORT" == "1" || "$REFRESH_REPORT" == "true" || "$REFRESH_REPORT" == "yes" || "$REFRESH_REPORT" == "on" ]]; then
  if ! ionice -c2 -n7 nice -n 15 env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.market_opportunity_census \
    --target-date "$TARGET_DATE" --write --print-summary 2>&1 | tee -a "$LOG_FILE"; then
    exit_code=${PIPESTATUS[0]}
    finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
    echo "[FAIL] market opportunity census target_date=${TARGET_DATE} phase=report exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
    exit "$exit_code"
  fi
fi

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] market opportunity census target_date=${TARGET_DATE} venues=${venues} refresh_report=${REFRESH_REPORT} runtime_effect=false finished_at=${finished_at}" | tee -a "$LOG_FILE"
