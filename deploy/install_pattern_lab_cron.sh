#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/PATTERN_LAB_CLAUDE_FRI_POSTCLOSE/ && !/PATTERN_LAB_GEMINI_FRI_POSTCLOSE/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# pattern lab weekly cron
40 18 * * 5 $PROJECT_DIR/deploy/run_claude_scalping_pattern_lab_cron.sh >> $PROJECT_DIR/logs/claude_scalping_pattern_lab_cron.log 2>&1 # PATTERN_LAB_CLAUDE_FRI_POSTCLOSE
10 19 * * 5 $PROJECT_DIR/deploy/run_gemini_scalping_pattern_lab_cron.sh >> $PROJECT_DIR/logs/gemini_scalping_pattern_lab_cron.log 2>&1 # PATTERN_LAB_GEMINI_FRI_POSTCLOSE
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
