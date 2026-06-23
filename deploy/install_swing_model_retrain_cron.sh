#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/KORStockScan}"
TMP_CRON="$(mktemp)"
crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/swing model retrain automation/ && !/SWING_MODEL_RETRAIN_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
cat >> "$TMP_CRON.filtered" <<CRON
# swing model retrain automation
55 21 * * 1-5 KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE=true $PROJECT_DIR/auto_retrain_pipeline.sh \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/swing_model_retrain_cron.log 2>&1 # SWING_MODEL_RETRAIN_POSTCLOSE
CRON
crontab "$TMP_CRON.filtered"
rm -f "$TMP_CRON" "$TMP_CRON.filtered"
echo "installed swing model retrain cron"
