#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
GCP_PUSH_HOST="${GCP_PUSH_HOST:-songstockscan.ddns.net}"
GCP_PUSH_USER="${GCP_PUSH_USER:-windy80xyt}"
GCP_PUSH_PROJECT_DIR="${GCP_PUSH_PROJECT_DIR:-/home/windy80xyt/KORStockScan}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/GCP_PREOPEN_ARTIFACT_PUSH/ && !/gcp preopen artifact push/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF_CRON
# gcp preopen artifact push
37 7 * * 1-5 GCP_PUSH_HOST=$GCP_PUSH_HOST GCP_PUSH_USER=$GCP_PUSH_USER GCP_PUSH_PROJECT_DIR=$GCP_PUSH_PROJECT_DIR $PROJECT_DIR/deploy/run_push_gcp_preopen_artifacts.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/gcp_preopen_artifact_push_cron.log 2>&1 # GCP_PREOPEN_ARTIFACT_PUSH
EOF_CRON

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
