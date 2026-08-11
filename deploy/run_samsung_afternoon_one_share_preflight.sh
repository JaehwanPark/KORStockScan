#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="$(/bin/date +%F)"

PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
  src.engine.automation.samsung_machine_entry_policy_apply \
  --target-date "$TARGET_DATE" \
  --write

for attempt in $(/usr/bin/seq 1 18); do
  if /usr/bin/tmux has-session -t bot 2>/dev/null; then
    if PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
      src.trading.samsung_afternoon_one_share.preflight \
      --target-date "$TARGET_DATE" \
      --main-bot-active \
      --write; then
      exit 0
    fi
  else
    echo "preflight attempt=$attempt main_bot_inactive"
  fi
  /bin/sleep 5
done

echo "Samsung afternoon one-share preflight failed after 18 attempts" >&2
exit 2
