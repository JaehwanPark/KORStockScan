#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
PROFILE="${1:-}"

case "$PROFILE" in
  samsung_heavy_midday)
    export KORSTOCKSCAN_LOW_PRICE_TWO_LEG_SAMSUNG_HEAVY_MIDDAY_ENABLED=true
    CONFIRM="010140_MIDDAY_TWO_LEG_LIVE"
    ;;
  samsung_heavy_afternoon)
    export KORSTOCKSCAN_LOW_PRICE_TWO_LEG_SAMSUNG_HEAVY_AFTERNOON_ENABLED=true
    CONFIRM="010140_AFTERNOON_TWO_LEG_LIVE"
    ;;
  sk_eternix_midday)
    export KORSTOCKSCAN_LOW_PRICE_TWO_LEG_SK_ETERNIX_MIDDAY_ENABLED=true
    CONFIRM="475150_MIDDAY_TWO_LEG_LIVE"
    ;;
  *)
    echo "unsupported low-price two-leg profile: $PROFILE" >&2
    exit 2
    ;;
esac

exec env PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
  src.trading.low_price_two_leg.service \
  --profile "$PROFILE" \
  --live \
  --confirm "$CONFIRM" \
  --interval-sec 2
