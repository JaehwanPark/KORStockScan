#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 5 || "$1" != "--owner" || "$3" != "--log" ]]; then
  echo "usage: $0 --owner OWNER --log LOG_PATH COMMAND [ARG ...]" >&2
  exit 2
fi

OWNER="$2"
LOG_PATH="$4"
shift 4
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$(dirname "$LOG_PATH")"

rotation_output=""
rotation_rc=0
rotation_output="$(bash "$SCRIPT_DIR/run_owned_log_rotation.sh" "$OWNER" "$LOG_PATH" 2>&1)" || rotation_rc=$?
if [[ -n "$rotation_output" ]]; then
  printf '%s\n' "$rotation_output" >>"$LOG_PATH"
fi
if [[ "$rotation_rc" -ne 0 ]]; then
  printf '[OWNED_LOG_ROTATION_WARNING] owner=%s log=%s exit_code=%s command_will_continue=true\n' \
    "$OWNER" "$LOG_PATH" "$rotation_rc" >>"$LOG_PATH"
fi

exec "$@" >>"$LOG_PATH" 2>&1
