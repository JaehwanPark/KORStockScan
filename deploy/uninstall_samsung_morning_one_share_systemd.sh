#!/usr/bin/env bash
set -euo pipefail

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

/bin/systemctl disable --now \
  korstockscan-samsung-morning-one-share.timer \
  korstockscan-samsung-one-share-preflight.timer || true
/bin/systemctl stop \
  korstockscan-samsung-morning-one-share.service \
  korstockscan-samsung-one-share-preflight.service || true
for unit in "${UNITS[@]}"; do
  /usr/bin/rm -f "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload

echo "removed only Samsung one-share units; widget service was not changed"
