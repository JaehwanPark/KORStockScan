#!/usr/bin/env bash
set -euo pipefail

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

/bin/systemctl disable --now \
  korstockscan-samsung-midday-one-share.timer \
  korstockscan-samsung-midday-one-share-preflight.timer || true
/bin/systemctl stop \
  korstockscan-samsung-midday-one-share.service \
  korstockscan-samsung-midday-one-share-preflight.service || true
for unit in "${UNITS[@]}"; do
  /usr/bin/rm -f "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload

echo "removed only midday units; morning, afternoon, and widget services were not changed"
