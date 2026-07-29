#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
RUNNER="$PROJECT_DIR/deploy/run_swing_live_dry_run_report.sh"
OPERATOR_OVERRIDE="${KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE:-false}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/swing live order dry-run report/ && !/SWING_LIVE_DRY_RUN_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

if [[ "$OPERATOR_OVERRIDE" == "true" || "$OPERATOR_OVERRIDE" == "1" ]]; then
  cat >> "$TMP_CRON" <<EOF
# swing live order dry-run report
15 20 * * 1-5 $RUNNER \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/swing_live_dry_run_cron.log 2>&1 # SWING_LIVE_DRY_RUN_POSTCLOSE
EOF
else
  echo "swing live order dry-run cron remains disabled; set KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE=true to install"
fi

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
