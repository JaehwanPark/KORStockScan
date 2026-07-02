#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '\
  !/update_kospi\.py/ && \
  !/DASHBOARD_DB_ARCHIVE_/ && \
  !/LOG_ROTATION_CLEANUP_/ && \
  !/Postclose evening ops window/ && \
  !/매일 밤 .*KOSPI 일봉 DB 업데이트/ && \
  !/dashboard DB archive/ && \
  !/run_logs_rotation_cleanup_cron\.sh/ \
' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# EOD data chain and early shutdown maintenance
# 20:05 is after the NXT close and keeps the data refresh parallel with postclose reporting.
5 20 * * 1-5 cd $PROJECT_DIR && $PROJECT_DIR/.venv/bin/python src/utils/update_kospi.py >> $PROJECT_DIR/logs/update_kospi.log 2>&1 # UPDATE_KOSPI_EOD_2005
50 20 * * 1-5 $PROJECT_DIR/deploy/run_dashboard_db_archive_cron.sh 0 >> $PROJECT_DIR/logs/dashboard_db_archive_cron.log 2>&1 # DASHBOARD_DB_ARCHIVE_2050
0 21 * * * $PROJECT_DIR/deploy/run_logs_rotation_cleanup_cron.sh 30 >> $PROJECT_DIR/logs/log_rotation_cleanup_cron.log 2>&1 # LOG_ROTATION_CLEANUP_2100
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
