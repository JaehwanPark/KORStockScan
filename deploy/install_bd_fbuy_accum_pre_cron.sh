#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '
  !/BD_FBUY_ACCUM_PRE_INTRADAY/ &&
  !/BD_FBUY_ACCUM_PRE_V1 DB-first dashboard scanner/
' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# BD_FBUY_ACCUM_PRE_V1 DB-first dashboard scanner, query-only
5,15,25,35,45,55 9-14 * * 1-5 $PROJECT_DIR/deploy/run_bd_fbuy_accum_pre_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/bd_fbuy_accum_pre_intraday_cron.log 2>&1 # BD_FBUY_ACCUM_PRE_INTRADAY
5,15,20 15 * * 1-5 $PROJECT_DIR/deploy/run_bd_fbuy_accum_pre_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/bd_fbuy_accum_pre_intraday_cron.log 2>&1 # BD_FBUY_ACCUM_PRE_INTRADAY
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
