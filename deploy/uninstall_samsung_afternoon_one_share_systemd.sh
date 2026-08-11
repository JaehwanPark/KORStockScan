#!/usr/bin/env bash
set -euo pipefail

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

/bin/systemctl disable --now \
  korstockscan-samsung-afternoon-one-share.timer \
  korstockscan-samsung-afternoon-one-share-preflight.timer || true
/bin/systemctl stop \
  korstockscan-samsung-afternoon-one-share.service \
  korstockscan-samsung-afternoon-one-share-preflight.service || true
for unit in "${UNITS[@]}"; do
  /usr/bin/rm -f "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload

echo "removed only afternoon units; morning and widget services were not changed"
