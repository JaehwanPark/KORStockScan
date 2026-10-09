#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/eod_terminal_gate.sh"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
RETENTION_DAYS="${1:-1}"
TARGET_DATE="${TARGET_DATE:-$(TZ=Asia/Seoul date +%F)}"

source_calendar_state="$(postclose_source_calendar_state "$PROJECT_DIR" "$VENV_PY" "$TARGET_DATE")"
if [[ "$source_calendar_state" == "non_trading" ]]; then
  printf '[SKIP] dashboard_db_archive target_date=%s reason=non_trading_source_date no_archive_mutation=true\n' "$TARGET_DATE"
  exit 0
fi
[[ "$source_calendar_state" == "trading" ]] || exit 2

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] dashboard_db_archive target_date=${TARGET_DATE} retention_days=${RETENTION_DAYS} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] dashboard_db_archive target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR
wait_for_eod_terminal "$PROJECT_DIR" "$TARGET_DATE" dashboard_db_archive \
  "${DASHBOARD_ARCHIVE_EOD_WAIT_SEC:-5400}" "${DASHBOARD_ARCHIVE_EOD_WAIT_INTERVAL_SEC:-30}"
PYTHONPATH=. "$VENV_PY" -m src.engine.compress_db_backfilled_files --days "$RETENTION_DAYS" >> "$PROJECT_DIR/logs/dashboard_db_archive.log" 2>&1
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] dashboard_db_archive target_date=${TARGET_DATE} retention_days=${RETENTION_DAYS} finished_at=${finished_at}"
