#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd -P)}"
LOCK_PATH="$PROJECT_DIR/data/runtime/runtime_release_set.lock"
SELECTION_LOCK_PATH="$PROJECT_DIR/data/runtime/runtime_release_selection.lock"

if (($# == 0)); then
  echo "usage: $0 command [args...]" >&2
  exit 2
fi
if [[ ! -d "$(dirname "$LOCK_PATH")" ]]; then
  echo "runtime_release_set_lock: runtime directory missing" >&2
  exit 2
fi
/usr/bin/touch "$LOCK_PATH"
/usr/bin/chmod 0666 "$LOCK_PATH"
/usr/bin/touch "$SELECTION_LOCK_PATH"
/usr/bin/chmod 0666 "$SELECTION_LOCK_PATH"
exec /usr/bin/flock -n "$LOCK_PATH" /usr/bin/flock -n "$SELECTION_LOCK_PATH" "$@"
