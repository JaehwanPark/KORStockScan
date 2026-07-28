#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/panic buying intraday report-only/ && !/PANIC_BUYING_0905_0955/ && !/PANIC_BUYING_1000_1455/ && !/PANIC_BUYING_1500_1530/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

crontab "$TMP_CRON"
echo "[DISABLED] panic buying cron removed; explicit operator instruction and override are required to restore it"
crontab -l | sed -n '1,280p'
