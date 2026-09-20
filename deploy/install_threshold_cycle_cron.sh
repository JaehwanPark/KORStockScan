#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/threshold cycle daily automation/ && !/THRESHOLD_CYCLE_PREOPEN/ && !/THRESHOLD_CYCLE_INTRADAY_CALIBRATION/ && !/SCALP_SIM_OVERNIGHT_PRECLOSE/ && !/THRESHOLD_CYCLE_POSTCLOSE/ && !/AI_ENTRY_SETUP_PAIRED_REPLAY_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# threshold cycle daily automation
35 7 * * 1-5 THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live THRESHOLD_CYCLE_AUTO_APPLY=true THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true bash $PROJECT_DIR/deploy/run_runtime_release.sh preopen \$(TZ=Asia/Seoul date +\\%F) # THRESHOLD_CYCLE_PREOPEN
10 20 * * 1-5 THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false bash $PROJECT_DIR/deploy/run_runtime_release.sh postclose \$(TZ=Asia/Seoul date +\\%F) # THRESHOLD_CYCLE_POSTCLOSE
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
