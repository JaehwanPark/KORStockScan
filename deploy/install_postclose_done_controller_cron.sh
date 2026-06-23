#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
RUNNER="$PROJECT_DIR/deploy/run_postclose_done_controller.sh"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/POSTCLOSE_DONE_CONTROLLER/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# postclose DONE controller and Codex workorder runner
40 21 * * 1-5 $RUNNER \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/postclose_done_controller_cron.log 2>&1 # POSTCLOSE_DONE_CONTROLLER
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
