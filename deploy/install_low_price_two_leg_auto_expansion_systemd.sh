#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-low-price-two-leg-auto-expansion.service
  korstockscan-low-price-two-leg-auto-expansion.timer
)

for unit in "${UNITS[@]}"; do
  /usr/bin/install -o root -g root -m 0644 "$SOURCE_DIR/$unit" "$TARGET_DIR/$unit"
done
/usr/bin/systemctl daemon-reload
/usr/bin/systemctl enable korstockscan-low-price-two-leg-auto-expansion.timer
