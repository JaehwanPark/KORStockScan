#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
PYTHON_BIN="${KORSTOCKSCAN_PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
EOD_WAIT_REQUIRED="${KORSTOCKSCAN_WIDGET_EVALUATION_WAIT_FOR_EOD:-true}"
EOD_WAIT_SEC="${KORSTOCKSCAN_WIDGET_EVALUATION_EOD_WAIT_SEC:-5400}"
EOD_WAIT_INTERVAL_SEC="${KORSTOCKSCAN_WIDGET_EVALUATION_EOD_WAIT_INTERVAL_SEC:-30}"

cd "$PROJECT_DIR"
export PYTHONPATH="${PYTHONPATH:-$PROJECT_DIR}"

completed_target_date="$(
  "$PYTHON_BIN" -c 'from src.engine.monitoring.widget_auto_trade_policy_calibration import resolve_completed_policy_target_date; print(resolve_completed_policy_target_date().isoformat())' \
    | tail -n 1
)"
if [[ ! "$completed_target_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  printf '[WIDGET_EVALUATION] invalid completed target date=%s\n' \
    "${completed_target_date:-missing}" >&2
  exit 2
fi

wait_for_eod_terminal() {
  if [[ "$EOD_WAIT_REQUIRED" != "true" && "$EOD_WAIT_REQUIRED" != "1" ]]; then
    printf '[WIDGET_EVALUATION] EOD gate skipped target_date=%s\n' \
      "$completed_target_date"
    return 0
  fi
  if [[ ! "$EOD_WAIT_SEC" =~ ^[0-9]+$ ]]; then
    EOD_WAIT_SEC=5400
  fi
  if [[ ! "$EOD_WAIT_INTERVAL_SEC" =~ ^[1-9][0-9]*$ ]]; then
    EOD_WAIT_INTERVAL_SEC=30
  fi

  local status_path="$PROJECT_DIR/data/runtime/update_kospi_status/update_kospi_${completed_target_date}.json"
  local waited=0
  local status="missing"
  local artifact_target_date=""
  local latest_quote_date=""
  local rows_on_latest_date=0
  while true; do
    if [[ -f "$status_path" ]]; then
      status="$(jq -r '.status // "invalid"' "$status_path" 2>/dev/null || printf 'invalid')"
      artifact_target_date="$(jq -r '.target_date // ""' "$status_path" 2>/dev/null || true)"
      latest_quote_date="$(jq -r '.db_state.latest_quote_date // ""' "$status_path" 2>/dev/null || true)"
      rows_on_latest_date="$(jq -r '.db_state.rows_on_latest_date // 0' "$status_path" 2>/dev/null || printf '0')"
      if [[ "$status" == "completed" || "$status" == "completed_with_warnings" ]]; then
        if [[ "$artifact_target_date" == "$completed_target_date" && "$latest_quote_date" == "$completed_target_date" && "$rows_on_latest_date" =~ ^[0-9]+$ && "$rows_on_latest_date" -gt 0 ]]; then
          printf '[WIDGET_EVALUATION] EOD ready target_date=%s waited=%ss rows=%s\n' \
            "$completed_target_date" "$waited" "$rows_on_latest_date"
          return 0
        fi
        printf '[WIDGET_EVALUATION] EOD terminal contract mismatch target_date=%s artifact_target_date=%s status=%s latest_quote_date=%s rows=%s\n' \
          "$completed_target_date" "${artifact_target_date:-missing}" "$status" "${latest_quote_date:-missing}" \
          "$rows_on_latest_date" >&2
        return 1
      fi
      if [[ "$status" == "failed" || "$status" == "fail" || "$status" == "error" ]]; then
        printf '[WIDGET_EVALUATION] EOD failed target_date=%s status=%s\n' \
          "$completed_target_date" "$status" >&2
        return 1
      fi
    fi
    if [[ "$waited" -ge "$EOD_WAIT_SEC" ]]; then
      printf '[WIDGET_EVALUATION] EOD wait timeout target_date=%s waited=%ss status=%s\n' \
        "$completed_target_date" "$waited" "$status" >&2
      return 1
    fi
    if [[ "$waited" -eq 0 ]]; then
      printf '[WIDGET_EVALUATION] waiting for EOD target_date=%s status=%s\n' \
        "$completed_target_date" "$status"
    fi
    sleep "$EOD_WAIT_INTERVAL_SEC"
    waited=$((waited + EOD_WAIT_INTERVAL_SEC))
  done
}

"$PYTHON_BIN" -m src.engine.monitoring.widget_advisory_calibration \
  --target-date "$completed_target_date" \
  --write
"$PYTHON_BIN" -m src.engine.monitoring.widget_auto_trade_policy_calibration \
  --target-date "$completed_target_date" \
  --write
wait_for_eod_terminal
"$PYTHON_BIN" -m src.engine.monitoring.widget_symbol_signal_policy_research \
  --end-date "$completed_target_date" \
  --write
"$PYTHON_BIN" -m src.engine.monitoring.widget_symbol_runtime_policy \
  --target-date "$completed_target_date" \
  --write

printf '[WIDGET_EVALUATION] completed target_date=%s\n' "$completed_target_date"
