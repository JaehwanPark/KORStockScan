#!/usr/bin/env bash
set -euo pipefail

# Request a graceful bot restart through the runtime-owned restart flag.
#
# Expected supervisor:
#   src/run_bot.sh
#
# Flow:
#   1. Touch restart.flag in the project root.
#   2. bot_main.py detects the flag, removes it, and exits with SIGTERM.
#   3. src/run_bot.sh observes the exit and starts bot_main.py again after its
#      normal delay.
#
# This script intentionally does not use pkill/kill -9, does not start a second
# bot process directly, and does not mutate runtime threshold/provider/order env.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESTART_FLAG="$PROJECT_DIR/restart.flag"
BOT_PATTERN="${KORSTOCKSCAN_BOT_PROCESS_PATTERN:-python.*bot_main.py}"
STOP_TIMEOUT_SEC="${KORSTOCKSCAN_GRACEFUL_RESTART_STOP_TIMEOUT_SEC:-90}"
START_TIMEOUT_SEC="${KORSTOCKSCAN_GRACEFUL_RESTART_START_TIMEOUT_SEC:-150}"
POLL_SEC="${KORSTOCKSCAN_GRACEFUL_RESTART_POLL_SEC:-2}"

bot_pids() {
    pgrep -f "$BOT_PATTERN" 2>/dev/null | sort -n || true
}

contains_pid() {
    local needle="$1"
    shift || true
    local item
    for item in "$@"; do
        if [ "$item" = "$needle" ]; then
            return 0
        fi
    done
    return 1
}

readarray -t OLD_PIDS < <(bot_pids)
if [ "${#OLD_PIDS[@]}" -eq 0 ]; then
    echo "No running bot_main.py process found. Not creating a restart request."
    echo "Start the supervised bot with: cd $PROJECT_DIR/src && ./run_bot.sh"
    exit 1
fi

echo "Requesting graceful bot restart via $RESTART_FLAG"
echo "Current bot PID(s): ${OLD_PIDS[*]}"
touch "$RESTART_FLAG"

elapsed=0
while [ "$elapsed" -lt "$STOP_TIMEOUT_SEC" ]; do
    readarray -t CURRENT_PIDS < <(bot_pids)
    still_old=false
    for pid in "${CURRENT_PIDS[@]}"; do
        if contains_pid "$pid" "${OLD_PIDS[@]}"; then
            still_old=true
            break
        fi
    done
    if [ "$still_old" = false ]; then
        echo "Previous bot PID exited."
        break
    fi
    sleep "$POLL_SEC"
    elapsed=$((elapsed + POLL_SEC))
done

if [ "$elapsed" -ge "$STOP_TIMEOUT_SEC" ]; then
    echo "Timed out waiting for previous bot PID to exit. Leaving restart.flag in place for bot_main.py."
    exit 2
fi

elapsed=0
while [ "$elapsed" -lt "$START_TIMEOUT_SEC" ]; do
    readarray -t CURRENT_PIDS < <(bot_pids)
    for pid in "${CURRENT_PIDS[@]}"; do
        if ! contains_pid "$pid" "${OLD_PIDS[@]}"; then
            echo "Graceful restart completed. New bot PID: $pid"
            exit 0
        fi
    done
    sleep "$POLL_SEC"
    elapsed=$((elapsed + POLL_SEC))
done

echo "Previous bot exited, but no new bot_main.py PID appeared before timeout."
echo "Check that src/run_bot.sh is the active supervisor and inspect logs/bot_history.log."
exit 3
