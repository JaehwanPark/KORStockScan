#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
RUNNER="$PROJECT_DIR/deploy/run_shadow_canary_check.sh"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true

awk '!/SHADOW_CANARY_PREOPEN/ && !/SHADOW_CANARY_OPEN_CHECK/ && !/SHADOW_CANARY_MIDMORNING/ && !/SHADOW_CANARY_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# WATCHING 75 shadow canary checks
5 8 * * 1-5 $RUNNER preopen \$(date +\\%F) >> $PROJECT_DIR/logs/shadow_canary_cron.log 2>&1 # SHADOW_CANARY_PREOPEN
5 9 * * 1-5 $RUNNER open_check \$(date +\\%F) >> $PROJECT_DIR/logs/shadow_canary_cron.log 2>&1 # SHADOW_CANARY_OPEN_CHECK
25 10 * * 1-5 $RUNNER midmorning \$(date +\\%F) >> $PROJECT_DIR/logs/shadow_canary_cron.log 2>&1 # SHADOW_CANARY_MIDMORNING
45 15 * * 1-5 $RUNNER postclose \$(date +\\%F) >> $PROJECT_DIR/logs/shadow_canary_cron.log 2>&1 # SHADOW_CANARY_POSTCLOSE
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,220p'
