#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd -P)}"
source "$SCRIPT_DIR/runtime_release_set_lock.sh"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-samsung-midday-one-share-preflight.service
  korstockscan-samsung-midday-one-share-preflight.timer
  korstockscan-samsung-midday-one-share.service
  korstockscan-samsung-midday-one-share.timer
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

runtime_release_set_lock_acquire "$PROJECT_DIR"

/bin/systemd-analyze verify "${UNITS[@]/#/$SYSTEMD_DIR/}"
/usr/bin/test -x "$SCRIPT_DIR/run_samsung_midday_one_share_preflight.sh"
for unit in "${UNITS[@]}"; do
  /usr/bin/install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload
/bin/systemctl enable --now \
  korstockscan-samsung-midday-one-share-preflight.timer \
  korstockscan-samsung-midday-one-share.timer
/bin/systemctl list-timers --all --no-pager \
  korstockscan-samsung-midday-one-share-preflight.timer \
  korstockscan-samsung-midday-one-share.timer

echo "installed only midday units; morning, afternoon, and widget services were not changed"
