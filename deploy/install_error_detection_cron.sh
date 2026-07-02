#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true

if grep -q "run_error_detection" "$TMP_CRON"; then
    echo "[INSTALL] error detection cron already installed. Updating..."
    awk '!/run_error_detection/' "$TMP_CRON" > "$TMP_CRON.filtered"
    mv "$TMP_CRON.filtered" "$TMP_CRON"
fi

cat >> "$TMP_CRON" <<EOF
*/5 7-21 * * 1-5 bash $PROJECT_DIR/deploy/run_error_detection.sh full >> $PROJECT_DIR/logs/run_error_detection_cron.log 2>&1 # ERROR_DETECTION_FULL
EOF

crontab "$TMP_CRON"
echo "[INSTALL] error detection cron installed: */5 7-21 * * 1-5"
crontab -l | grep run_error_detection
