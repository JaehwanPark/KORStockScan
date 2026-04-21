#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
RUNNER="$PROJECT_DIR/deploy/run_tuning_monitoring_postclose.sh"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/TUNING_MONITORING_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# tuning monitoring parquet/DuckDB postclose sync
0 18 * * 1-5 $RUNNER \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/tuning_monitoring_postclose_cron.log 2>&1 # TUNING_MONITORING_POSTCLOSE
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
