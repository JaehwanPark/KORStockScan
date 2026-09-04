#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-symbol-owner-policy-auto-apply.service
  korstockscan-symbol-owner-policy-auto-apply.timer
  korstockscan-widget-signal-auto-trader.service
  korstockscan-samsung-morning-one-share.service
  korstockscan-samsung-one-share-preflight.service
  korstockscan-samsung-midday-one-share.service
  korstockscan-samsung-midday-one-share-preflight.service
  korstockscan-samsung-afternoon-one-share.service
  korstockscan-samsung-afternoon-one-share-preflight.service
  korstockscan-low-price-two-leg@.service
  korstockscan-low-price-two-leg-preflight@.service
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

for unit in "${UNITS[@]}"; do
  install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done

systemctl daemon-reload
systemctl enable --now korstockscan-symbol-owner-policy-auto-apply.timer

echo "installed and enabled the 07:32 exact-date symbol-owner auto-apply timer"
echo "running trading services were not restarted by this installer"
