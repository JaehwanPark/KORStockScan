#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-samsung-afternoon-one-share-preflight.service
  korstockscan-samsung-afternoon-one-share-preflight.timer
  korstockscan-samsung-afternoon-one-share.service
  korstockscan-samsung-afternoon-one-share.timer
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

/bin/systemd-analyze verify "${UNITS[@]/#/$SYSTEMD_DIR/}"
/usr/bin/test -x "$SCRIPT_DIR/run_samsung_afternoon_one_share_preflight.sh"
for unit in "${UNITS[@]}"; do
  /usr/bin/install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload
/bin/systemctl enable --now \
  korstockscan-samsung-afternoon-one-share-preflight.timer \
  korstockscan-samsung-afternoon-one-share.timer
/bin/systemctl list-timers --all --no-pager \
  korstockscan-samsung-afternoon-one-share-preflight.timer \
  korstockscan-samsung-afternoon-one-share.timer

echo "installed only afternoon units; morning and widget services were not changed"
