#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-samsung-one-share-preflight.service
  korstockscan-samsung-one-share-preflight.timer
  korstockscan-samsung-morning-one-share.service
  korstockscan-samsung-morning-one-share.timer
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

/bin/systemd-analyze verify "${UNITS[@]/#/$SYSTEMD_DIR/}"
for unit in "${UNITS[@]}"; do
  /usr/bin/install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done

/bin/systemctl daemon-reload
/bin/systemctl enable --now \
  korstockscan-samsung-one-share-preflight.timer \
  korstockscan-samsung-morning-one-share.timer

/bin/systemctl list-timers --all --no-pager \
  korstockscan-samsung-one-share-preflight.timer \
  korstockscan-samsung-morning-one-share.timer

echo "installed; widget service was not changed or restarted"
