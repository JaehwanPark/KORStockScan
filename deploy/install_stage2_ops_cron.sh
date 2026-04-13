#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/REMOTE_LATENCY_BASELINE_PREOPEN/ && !/REMOTE_LATENCY_BASELINE_MIDMORNING/ && !/REMOTE_LATENCY_BASELINE_AFTERNOON/ && !/RUN_MONITOR_SNAPSHOT_1000/ && !/RUN_MONITOR_SNAPSHOT_1200/ && !/REMOTE_SCALPING_FETCH_1600/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# stage2 ops cron
20 8 * * 1-5 $PROJECT_DIR/deploy/run_remote_latency_baseline.sh preopen >> $PROJECT_DIR/logs/remote_latency_baseline_cron.log 2>&1 # REMOTE_LATENCY_BASELINE_PREOPEN
0 10 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_1000
20 10 * * 1-5 $PROJECT_DIR/deploy/run_remote_latency_baseline.sh midmorning >> $PROJECT_DIR/logs/remote_latency_baseline_cron.log 2>&1 # REMOTE_LATENCY_BASELINE_MIDMORNING
0 12 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_1200
20 13 * * 1-5 $PROJECT_DIR/deploy/run_remote_latency_baseline.sh afternoon >> $PROJECT_DIR/logs/remote_latency_baseline_cron.log 2>&1 # REMOTE_LATENCY_BASELINE_AFTERNOON
0 16 * * 1-5 $PROJECT_DIR/deploy/fetch_remote_scalping_logs_cron.sh >> $PROJECT_DIR/logs/remote_scalping_fetch_cron.log 2>&1 # REMOTE_SCALPING_FETCH_1600
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
