#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/threshold cycle daily automation/ && !/THRESHOLD_CYCLE_PREOPEN/ && !/THRESHOLD_CYCLE_INTRADAY_CALIBRATION/ && !/SCALP_SIM_OVERNIGHT_PRECLOSE/ && !/THRESHOLD_CYCLE_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# threshold cycle daily automation
35 7 * * 1-5 THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live THRESHOLD_CYCLE_AUTO_APPLY=true THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true $PROJECT_DIR/deploy/run_threshold_cycle_preopen.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/threshold_cycle_preopen_cron.log 2>&1 # THRESHOLD_CYCLE_PREOPEN
20 15 * * 1-5 $PROJECT_DIR/deploy/run_scalp_sim_overnight_preclose.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/scalp_sim_overnight_preclose_cron.log 2>&1 # SCALP_SIM_OVERNIGHT_PRECLOSE
10 16 * * 1-5 THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart $PROJECT_DIR/deploy/run_threshold_cycle_postclose.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/threshold_cycle_postclose_cron.log 2>&1 # THRESHOLD_CYCLE_POSTCLOSE
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
