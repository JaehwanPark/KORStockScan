#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/REMOTE_LATENCY_BASELINE_PREOPEN/ && !/REMOTE_LATENCY_BASELINE_MIDMORNING/ && !/REMOTE_LATENCY_BASELINE_AFTERNOON/ && !/RUN_MONITOR_SNAPSHOT_1000/ && !/RUN_MONITOR_SNAPSHOT_1200/ && !/RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09/ && !/RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11/ && !/REMOTE_SCALPING_FETCH_1600/ && !/SYSTEM_METRIC_SAMPLER_1MIN/ && !/RISING_MISSED_INTRADAY_FEEDBACK_5MIN/ && !/SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# stage2 ops cron
* * * * 1-5 $PROJECT_DIR/deploy/run_system_metric_sampler_cron.sh >> $PROJECT_DIR/logs/system_metric_sampler_cron.log 2>&1 # SYSTEM_METRIC_SAMPLER_1MIN
*/5 8-19 * * 1-5 $PROJECT_DIR/deploy/run_rising_missed_intraday_feedback.sh >> $PROJECT_DIR/logs/run_rising_missed_intraday_feedback_cron.log 2>&1 # RISING_MISSED_INTRADAY_FEEDBACK_5MIN
*/5 8-19 * * 1-5 $PROJECT_DIR/deploy/run_scalping_pyramid_intraday_feedback.sh >> $PROJECT_DIR/logs/run_scalping_pyramid_intraday_feedback_cron.log 2>&1 # SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN
35-55/20 9 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_incremental_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09
*/20 10-11 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_incremental_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11
0 12 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_1200
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
