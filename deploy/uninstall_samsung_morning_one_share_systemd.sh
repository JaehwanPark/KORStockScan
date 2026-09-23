#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
SCRIPT_DIR="$PROJECT_DIR/deploy"
source "$SCRIPT_DIR/runtime_release_set_lock.sh"

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

runtime_release_set_lock_acquire "$PROJECT_DIR"

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
