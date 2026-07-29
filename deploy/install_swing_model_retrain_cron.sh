#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/KORStockScan}"
OPERATOR_OVERRIDE="${KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE:-false}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON" "$TMP_CRON.filtered"' EXIT
crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/swing model retrain automation/ && !/SWING_MODEL_RETRAIN_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
if [[ "$OPERATOR_OVERRIDE" == "true" || "$OPERATOR_OVERRIDE" == "1" ]]; then
  cat >> "$TMP_CRON.filtered" <<CRON
# swing model retrain automation
10 21 * * 1-5 KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE=true $PROJECT_DIR/auto_retrain_pipeline.sh \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/swing_model_retrain_cron.log 2>&1 # SWING_MODEL_RETRAIN_POSTCLOSE
CRON
else
  echo "swing model retrain cron remains disabled; set KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE=true to install"
fi
crontab "$TMP_CRON.filtered"
echo "updated swing model retrain cron"
