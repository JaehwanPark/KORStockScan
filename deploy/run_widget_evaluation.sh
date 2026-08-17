#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
PYTHON_BIN="${KORSTOCKSCAN_PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"

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

"$PYTHON_BIN" -m src.engine.monitoring.widget_advisory_calibration \
  --target-date "$completed_target_date" \
  --write
"$PYTHON_BIN" -m src.engine.monitoring.widget_auto_trade_policy_calibration \
  --target-date "$completed_target_date" \
  --write
"$PYTHON_BIN" -m src.engine.monitoring.widget_symbol_signal_policy_research \
  --end-date "$completed_target_date" \
  --write
"$PYTHON_BIN" -m src.engine.monitoring.widget_symbol_runtime_policy \
  --target-date "$completed_target_date" \
  --write

printf '[WIDGET_EVALUATION] completed target_date=%s\n' "$completed_target_date"
