#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="$(TZ=Asia/Seoul /bin/date +%F)"
BOT_PATTERN="${KORSTOCKSCAN_BOT_PROCESS_PATTERN:-[/]python bot_main[.]py$}"
PREFLIGHT_DEADLINE_HHMMSS="${KORSTOCKSCAN_SAMSUNG_MORNING_PREFLIGHT_DEADLINE_HHMMSS:-09:25:00}"
POLL_SEC="${KORSTOCKSCAN_SAMSUNG_MORNING_PREFLIGHT_POLL_SEC:-5}"

if [[ ! "$PREFLIGHT_DEADLINE_HHMMSS" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$ ]]; then
  echo "Invalid Samsung morning preflight deadline: $PREFLIGHT_DEADLINE_HHMMSS" >&2
  exit 64
fi
if [[ ! "$POLL_SEC" =~ ^[1-9][0-9]*$ ]]; then
  echo "Invalid Samsung morning preflight poll seconds: $POLL_SEC" >&2
  exit 64
fi
if [ "$POLL_SEC" -gt 60 ]; then
  echo "Samsung morning preflight poll seconds exceed bounded maximum: $POLL_SEC" >&2
  exit 64
fi

deadline_elapsed() {
  local now_hhmmss
  now_hhmmss="$(TZ=Asia/Seoul /bin/date +%H:%M:%S)"
  [[ "$now_hhmmss" > "$PREFLIGHT_DEADLINE_HHMMSS" ]] || \
    [[ "$now_hhmmss" == "$PREFLIGHT_DEADLINE_HHMMSS" ]]
}

compact_verify_detail() {
  "$PYTHON_BIN" -c '
import json
import sys

raw = sys.stdin.read().strip()
payload = None
for line in reversed(raw.splitlines()):
    try:
        candidate = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        continue
    if isinstance(candidate, dict):
        payload = candidate
        break
if payload is None:
    print(json.dumps({"status": "unparseable", "output_length": len(raw)}))
else:
    keep = {
        key: payload.get(key)
        for key in (
            "target_date",
            "status",
            "fail_reason",
            "pid",
            "pid_env_available",
            "pid_env_read_error",
            "pid_passed",
            "missing_family_count",
            "runtime_policy_fail_count",
            "dated_runtime_override_fail_count",
            "unverified_selected_family_count",
        )
    }
    print(json.dumps(keep, ensure_ascii=True, separators=(",", ":")))
'
}

if deadline_elapsed; then
  echo "Samsung one-share preflight deadline elapsed target_date=$TARGET_DATE deadline=$PREFLIGHT_DEADLINE_HHMMSS" >&2
  exit 3
fi

PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
  src.engine.automation.samsung_machine_entry_policy_apply \
  --target-date "$TARGET_DATE" \
  --write

attempt=0
while true; do
  attempt=$((attempt + 1))
  if deadline_elapsed; then
    echo "Samsung one-share preflight deadline elapsed target_date=$TARGET_DATE deadline=$PREFLIGHT_DEADLINE_HHMMSS" >&2
    exit 3
  fi

  mapfile -t bot_pids < <(/usr/bin/pgrep -f "$BOT_PATTERN" 2>/dev/null | /usr/bin/sort -n || true)
  if ! /usr/bin/tmux has-session -t bot 2>/dev/null; then
    echo "preflight attempt=$attempt main_bot_supervisor_inactive"
  elif [ "${#bot_pids[@]}" -eq 0 ]; then
    echo "preflight attempt=$attempt main_bot_inactive"
  elif [ "${#bot_pids[@]}" -ne 1 ]; then
    echo "preflight attempt=$attempt main_bot_pid_count_invalid count=${#bot_pids[@]} pids=${bot_pids[*]}"
  else
    bot_pid="${bot_pids[0]}"
    verify_output=""
    if verify_output="$(
      PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
        src.engine.threshold_cycle_preopen_apply \
        --verify \
        --target-date "$TARGET_DATE" \
        --pid "$bot_pid" 2>&1
    )"; then
      if deadline_elapsed; then
        echo "Samsung one-share preflight deadline elapsed before verify commit target_date=$TARGET_DATE deadline=$PREFLIGHT_DEADLINE_HHMMSS" >&2
        exit 3
      fi
      verify_commit_output=""
      if verify_commit_output="$(
        PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
          src.engine.threshold_cycle_preopen_apply \
          --verify \
          --target-date "$TARGET_DATE" \
          --pid "$bot_pid" \
          --write-verify-artifact 2>&1
      )"; then
        if deadline_elapsed; then
          echo "Samsung one-share preflight deadline elapsed before authority write target_date=$TARGET_DATE deadline=$PREFLIGHT_DEADLINE_HHMMSS" >&2
          exit 3
        fi
        if PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
          src.trading.samsung_morning_one_share.preflight \
          --target-date "$TARGET_DATE" \
          --main-bot-active \
          --main-bot-pid "$bot_pid" \
          --authority-deadline-hhmmss "$PREFLIGHT_DEADLINE_HHMMSS" \
          --write; then
          echo "Samsung one-share preflight passed target_date=$TARGET_DATE bot_pid=$bot_pid runtime_env_verified=true"
          exit 0
        fi
      else
        verify_commit_detail="$(compact_verify_detail <<<"$verify_commit_output")"
        echo "preflight attempt=$attempt main_bot_runtime_env_verify_commit_failed bot_pid=$bot_pid detail=$verify_commit_detail"
      fi
    else
      verify_detail="$(compact_verify_detail <<<"$verify_output")"
      echo "preflight attempt=$attempt main_bot_runtime_env_unverified bot_pid=$bot_pid detail=$verify_detail"
    fi
  fi
  /bin/sleep "$POLL_SEC"
done
