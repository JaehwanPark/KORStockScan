#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
OUT_DIR="$PROJECT_DIR/tmp/remote_latency_baseline"

WINDOW="${1:?window required}"
TARGET_DATE="${2:-$(TZ=Asia/Seoul date +%F)}"

mkdir -p "$LOG_DIR" "$OUT_DIR"
cd "$PROJECT_DIR"

set +e
RESULT=$(PYTHONPATH=. "$VENV_PY" -m src.engine.collect_remote_latency_baseline \
  --date "$TARGET_DATE" \
  --window "$WINDOW" 2>&1)
EXIT_CODE=$?
set -e

printf '%s\n' "$RESULT" >> "$LOG_DIR/remote_latency_baseline.log"
printf '[REMOTE_LATENCY_BASELINE] window=%s date=%s exit=%s\n' "$WINDOW" "$TARGET_DATE" "$EXIT_CODE" >> "$LOG_DIR/remote_latency_baseline_cron.log"
printf '%s\n' "$RESULT" >> "$LOG_DIR/remote_latency_baseline_cron.log"
exit 0
