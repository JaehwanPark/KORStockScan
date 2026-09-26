#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true

if grep -Eq 'run_error_detection|ERROR_DETECTION_FULL' "$TMP_CRON"; then
    echo "[INSTALL] error detection cron already installed. Updating..."
    # Finalization is owned by the release-routed stage2 cron installer.  An
    # error-detector reinstall must never replace or delete that owner.
    awk '!/run_error_detection/ && !/ERROR_DETECTION_FULL/' "$TMP_CRON" > "$TMP_CRON.filtered"
    mv "$TMP_CRON.filtered" "$TMP_CRON"
fi

cat >> "$TMP_CRON" <<EOF
*/5 7-20 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner error_detection_cron --log $PROJECT_DIR/logs/run_error_detection_cron.log bash $PROJECT_DIR/deploy/run_error_detection.sh full # ERROR_DETECTION_FULL
0-50/5 21 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner error_detection_cron --log $PROJECT_DIR/logs/run_error_detection_cron.log bash $PROJECT_DIR/deploy/run_error_detection.sh full # ERROR_DETECTION_FULL
EOF

crontab "$TMP_CRON"
echo "[INSTALL] error detection cron installed: */5 07:00-21:50; finalization owner preserved"
crontab -l | grep -E 'ERROR_DETECTION_FULL'
