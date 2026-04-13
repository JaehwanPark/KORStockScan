#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
PYTHONPATH=. "$VENV_PY" -m src.engine.fetch_remote_scalping_logs \
  --date "$TARGET_DATE" \
  --include-snapshots-if-exist \
  --snapshot-only-on-live-failure \
  >> "$PROJECT_DIR/logs/remote_scalping_fetch.log" 2>&1
