#!/usr/bin/env bash
set -euo pipefail

# Cleanup-only shim for retired weekly jobs. It never installs a Lab job.
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '
  /PATTERN_LAB_CLAUDE_FRI_POSTCLOSE/ {next}
  /PATTERN_LAB_GEMINI_FRI_POSTCLOSE/ {next}
  /^# pattern lab weekly cron$/ {next}
  {print}
' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

crontab "$TMP_CRON"
echo "Retired weekly Lab cron markers removed; no jobs installed."
