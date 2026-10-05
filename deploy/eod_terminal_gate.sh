#!/usr/bin/env bash

# Shared exact-date gate for compute-heavy postclose consumers.
postclose_source_calendar_state() {
  local project_dir="$1" python_bin="$2" target_date="$3"
  (cd "$project_dir" && PYTHONPATH=. "$python_bin" - "$target_date" <<'PY'
import sys
from datetime import date
from src.utils.market_day import is_krx_trading_day
day = date.fromisoformat(sys.argv[1])
if day.isoformat() != sys.argv[1]:
    raise ValueError('postclose_source_date_not_canonical')
print('trading' if is_krx_trading_day(day) else 'non_trading')
PY
  )
}

wait_for_eod_terminal() {
  local project_dir="$1"
  local target_date="$2"
  local owner="${3:-postclose}"
  local wait_sec="${4:-5400}"
  local interval_sec="${5:-30}"
  local status_path="$project_dir/data/runtime/update_kospi_status/update_kospi_${target_date}.json"
  local waited=0
  local status="missing"
  local artifact_target_date=""
  local latest_quote_date=""
  local rows_on_latest_date=0

  if [[ ! "$wait_sec" =~ ^[0-9]+$ || ! "$interval_sec" =~ ^[1-9][0-9]*$ ]]; then
    printf '[%s] EOD gate invalid wait configuration target_date=%s\n' "$owner" "$target_date" >&2
    return 2
  fi
  while true; do
    if [[ -f "$status_path" ]]; then
      status="$(jq -r '.status // "invalid"' "$status_path" 2>/dev/null || printf 'invalid')"
      artifact_target_date="$(jq -r '.target_date // ""' "$status_path" 2>/dev/null || true)"
      latest_quote_date="$(jq -r '.db_state.latest_quote_date // ""' "$status_path" 2>/dev/null || true)"
      rows_on_latest_date="$(jq -r '.db_state.rows_on_latest_date // 0' "$status_path" 2>/dev/null || printf '0')"
      if [[ "$status" == "completed" || "$status" == "completed_with_warnings" ]]; then
        if [[ "$artifact_target_date" == "$target_date" && "$latest_quote_date" == "$target_date" && "$rows_on_latest_date" =~ ^[0-9]+$ && "$rows_on_latest_date" -gt 0 ]]; then
          printf '[%s] EOD ready target_date=%s waited=%ss rows=%s status=%s\n' \
            "$owner" "$target_date" "$waited" "$rows_on_latest_date" "$status"
          return 0
        fi
        printf '[%s] EOD terminal contract mismatch target_date=%s artifact_target_date=%s status=%s latest_quote_date=%s rows=%s\n' \
          "$owner" "$target_date" "${artifact_target_date:-missing}" "$status" "${latest_quote_date:-missing}" "$rows_on_latest_date" >&2
        return 1
      fi
      if [[ "$status" == "failed" || "$status" == "fail" || "$status" == "error" ]]; then
        printf '[%s] EOD failed target_date=%s status=%s\n' "$owner" "$target_date" "$status" >&2
        return 1
      fi
    fi
    if (( waited >= wait_sec )); then
      printf '[%s] EOD wait timeout target_date=%s waited=%ss status=%s\n' "$owner" "$target_date" "$waited" "$status" >&2
      return 1
    fi
    if (( waited == 0 )); then
      printf '[%s] waiting for exact-date EOD terminal target_date=%s status=%s\n' "$owner" "$target_date" "$status"
    fi
    sleep "$interval_sec"
    waited=$((waited + interval_sec))
  done
}
