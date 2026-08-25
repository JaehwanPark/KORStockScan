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
#   3. If the running supervisor loaded a different run_bot.sh generation,
#      replace only the drained tmux supervisor before starting bot_main.py.
#   4. Otherwise src/run_bot.sh observes the exit and starts bot_main.py again
#      after its normal delay.
#
# This script intentionally does not use pkill/kill -9, does not start a second
# bot process while the old child is alive, and does not mutate runtime
# threshold/provider/order env.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="${KORSTOCKSCAN_VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
RESTART_FLAG="$PROJECT_DIR/restart.flag"
RESTART_REQUEST_TMP="${RESTART_FLAG}.$$"
RESTART_SOURCE="${KORSTOCKSCAN_RESTART_REQUEST_SOURCE:-operator_restart_sh}"
# Anchor the default pattern to the real bot command.  Broad patterns such as
# "python.*bot_main.py" also match monitor shells whose command text contains a
# pgrep expression, which can make a healthy graceful restart look stuck.
BOT_PATTERN="${KORSTOCKSCAN_BOT_PROCESS_PATTERN:-[/]python bot_main[.]py$}"
STOP_TIMEOUT_SEC="${KORSTOCKSCAN_GRACEFUL_RESTART_STOP_TIMEOUT_SEC:-90}"
START_TIMEOUT_SEC="${KORSTOCKSCAN_GRACEFUL_RESTART_START_TIMEOUT_SEC:-150}"
POLL_SEC="${KORSTOCKSCAN_GRACEFUL_RESTART_POLL_SEC:-2}"
BOT_TMUX_SESSION="${KORSTOCKSCAN_BOT_TMUX_SESSION:-bot}"
RUN_BOT_PATH="$PROJECT_DIR/src/run_bot.sh"
trap 'rm -f "$RESTART_REQUEST_TMP"' EXIT

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

pid_env_value() {
    local pid="$1"
    local key="$2"
    tr '\0' '\n' < "/proc/${pid}/environ" 2>/dev/null \
        | sed -n "s/^${key}=//p" \
        | head -n 1
}

current_launcher_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$RUN_BOT_PATH" | awk '{print $1}'
        return
    fi
    printf '%s\n' unknown
}

restart_drained_tmux_supervisor() {
    local live_pids=()
    local kill_rc=0
    readarray -t live_pids < <(bot_pids)
    if [ "${#live_pids[@]}" -ne 0 ]; then
        echo "Refusing supervisor reload because a bot child is alive: ${live_pids[*]}" >&2
        return 1
    fi
    if ! command -v tmux >/dev/null 2>&1; then
        echo "tmux is required to reload the bot supervisor." >&2
        return 1
    fi
    if ! tmux has-session -t "$BOT_TMUX_SESSION" 2>/dev/null; then
        echo "Expected tmux supervisor session is missing: $BOT_TMUX_SESSION" >&2
        return 1
    fi
    echo "Reloading drained tmux supervisor session: $BOT_TMUX_SESSION"
    # Killing the final session also terminates the tmux server. Some tmux
    # versions report that expected server shutdown with a non-zero status, so
    # judge success from the scoped session state instead of the raw rc alone.
    set +e
    tmux kill-session -t "$BOT_TMUX_SESSION"
    kill_rc=$?
    set -e
    if tmux has-session -t "$BOT_TMUX_SESSION" 2>/dev/null; then
        echo "Bot tmux supervisor session survived reload request (rc=$kill_rc)." >&2
        return 1
    fi
    if [ "$kill_rc" -ne 0 ]; then
        echo "tmux server exited with the final session; confirmed session removal."
    fi
    tmux new-session -d -s "$BOT_TMUX_SESSION" \
        "/bin/bash -c \"cd $PROJECT_DIR/src && source ../.venv/bin/activate && exec ./run_bot.sh\""
}

readarray -t OLD_PIDS < <(bot_pids)
if [ "${#OLD_PIDS[@]}" -eq 0 ]; then
    echo "No running bot_main.py process found. Not creating a restart request."
    echo "Start the supervised bot with: cd $PROJECT_DIR/src && ./run_bot.sh"
    exit 1
fi

CURRENT_LAUNCHER_SHA256="$(current_launcher_sha256)"
LOADED_LAUNCHER_SHA256="$(pid_env_value "${OLD_PIDS[0]}" KORSTOCKSCAN_RUNTIME_LAUNCHER_RUN_BOT_SHA256 || true)"
RELOAD_SUPERVISOR=false
if [ -n "$LOADED_LAUNCHER_SHA256" ] \
    && [ "$LOADED_LAUNCHER_SHA256" != unknown ] \
    && [ "$CURRENT_LAUNCHER_SHA256" != unknown ] \
    && [ "$LOADED_LAUNCHER_SHA256" != "$CURRENT_LAUNCHER_SHA256" ]; then
    RELOAD_SUPERVISOR=true
    echo "Launcher generation drift detected; supervisor reload required."
    echo "Loaded run_bot.sh sha256: $LOADED_LAUNCHER_SHA256"
    echo "Current run_bot.sh sha256: $CURRENT_LAUNCHER_SHA256"
fi

echo "Requesting graceful bot restart via $RESTART_FLAG"
echo "Current bot PID(s): ${OLD_PIDS[*]}"
printf 'source=%s requested_at_utc=%s old_pids=%s\n' \
    "$RESTART_SOURCE" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${OLD_PIDS[*]}" \
    > "$RESTART_REQUEST_TMP"
mv -f "$RESTART_REQUEST_TMP" "$RESTART_FLAG"

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

if [ "$RELOAD_SUPERVISOR" = true ]; then
    restart_drained_tmux_supervisor
fi

elapsed=0
while [ "$elapsed" -lt "$START_TIMEOUT_SEC" ]; do
    readarray -t CURRENT_PIDS < <(bot_pids)
    for pid in "${CURRENT_PIDS[@]}"; do
        if ! contains_pid "$pid" "${OLD_PIDS[@]}"; then
            echo "Graceful restart completed. New bot PID: $pid"
            APPLICATION_DATE="${KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE:-$(date +%Y-%m-%d)}"
            echo "Verifying runtime env handoff for PID $pid ..."
            set +e
            VERIFY_RC=0
            PYTHONPATH="$PROJECT_DIR" "$VENV_PY" -m src.engine.threshold_cycle_preopen_apply \
                --verify --date "$APPLICATION_DATE" --pid "$pid" --write-verify-artifact || VERIFY_RC=$?
            set -e
            if [ "$VERIFY_RC" -ne 0 ]; then
                echo "[WARN] Runtime env handoff verification failed for PID $pid (rc=$VERIFY_RC)."
                echo "[WARN] Verification artifact written to data/threshold_cycle/runtime_env/threshold_runtime_env_verify_${APPLICATION_DATE}.json"
                exit "$VERIFY_RC"
            fi
            echo "Runtime env handoff verification passed."
            exit 0
        fi
    done
    sleep "$POLL_SEC"
    elapsed=$((elapsed + POLL_SEC))
done

echo "Previous bot exited, but no new bot_main.py PID appeared before timeout."
echo "Check that src/run_bot.sh is the active supervisor and inspect logs/bot_history.log."
exit 3
