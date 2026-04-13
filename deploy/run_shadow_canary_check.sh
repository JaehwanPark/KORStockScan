#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
OUT_DIR="$PROJECT_DIR/tmp/shadow_canary_checks"

PHASE="${1:?phase required}"
TARGET_DATE="${2:-$(date +%F)}"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$LOG_DIR" "$OUT_DIR"

JSON_OUT="$OUT_DIR/${TARGET_DATE}_${PHASE}_${TS}.json"
STDOUT_LOG="$LOG_DIR/shadow_canary_check.log"

cd "$PROJECT_DIR"
set +e
PYTHONPATH=. "$VENV_PY" -m src.engine.check_watching_prompt_75_shadow_canary \
  --date "$TARGET_DATE" \
  --phase "$PHASE" \
  > "$JSON_OUT"
CHECK_EXIT=$?
set -e

cat "$JSON_OUT" >> "$STDOUT_LOG"
printf '\n' >> "$STDOUT_LOG"

printf '[SHADOW_CANARY_CHECK] phase=%s date=%s json=%s exit=%s\n' "$PHASE" "$TARGET_DATE" "$JSON_OUT" "$CHECK_EXIT"
exit 0
