#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
PYTHONPATH=. "$VENV_PY" -m src.engine.fetch_remote_scalping_logs \
  --date "$TARGET_DATE" \
  --include-snapshots-if-exist \
  --snapshot-only-on-live-failure \
  >> "$PROJECT_DIR/logs/remote_scalping_fetch.log" 2>&1
