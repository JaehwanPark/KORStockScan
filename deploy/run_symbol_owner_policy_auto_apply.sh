#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
AUTHORITY_PATH="$PROJECT_DIR/data/config/symbol_owner_policy_standing_authority.json"
RESTORE_UNITS=()

restore_order_services() {
  local unit restore_rc=0
  for unit in "${RESTORE_UNITS[@]}"; do
    if systemctl is-active --quiet "$unit"; then
      continue
    fi
    if ! systemctl start "$unit"; then
      echo "[symbol-owner-auto-apply] failed to restore unit: $unit" >&2
      restore_rc=1
    fi
  done
  return "$restore_rc"
}

on_exit() {
  local original_rc=$?
  trap - EXIT
  if ! restore_order_services; then
    exit 3
  fi
  exit "$original_rc"
}

trap on_exit EXIT

while read -r unit _rest; do
  case "$unit" in
    korstockscan-widget-signal-auto-trader.service|\
    korstockscan-samsung-morning-one-share.service|\
    korstockscan-samsung-midday-one-share.service|\
    korstockscan-samsung-afternoon-one-share.service|\
    korstockscan-low-price-two-leg@*.service)
      RESTORE_UNITS+=("$unit")
      ;;
  esac
done < <(systemctl list-units --type=service --state=active --no-legend --plain)

for unit in "${RESTORE_UNITS[@]}"; do
  echo "[symbol-owner-auto-apply] stopping order service for quiescent apply: $unit"
  systemctl stop "$unit"
done

runuser --user ubuntu -- env \
  PYTHONPATH="$PROJECT_DIR" \
  "$PYTHON_BIN" -m src.trading.order.symbol_owner_policy_auto_apply \
  --standing-authority "$AUTHORITY_PATH"
