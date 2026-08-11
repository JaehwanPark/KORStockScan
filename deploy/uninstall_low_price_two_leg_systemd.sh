#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="/etc/systemd/system"
TIMERS=(
  korstockscan-low-price-two-leg-samsung-heavy-midday-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-midday.timer
  korstockscan-low-price-two-leg-samsung-heavy-afternoon-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-afternoon.timer
  korstockscan-low-price-two-leg-daewoo-ec-midday-preflight.timer
  korstockscan-low-price-two-leg-daewoo-ec-midday.timer
  korstockscan-low-price-two-leg-daewoo-ec-afternoon-preflight.timer
  korstockscan-low-price-two-leg-daewoo-ec-afternoon.timer
  korstockscan-low-price-two-leg-sk-eternix-midday-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-midday.timer
)
SERVICES=(
  korstockscan-low-price-two-leg@samsung_heavy_midday.service
  korstockscan-low-price-two-leg@samsung_heavy_afternoon.service
  korstockscan-low-price-two-leg@daewoo_ec_midday.service
  korstockscan-low-price-two-leg@daewoo_ec_afternoon.service
  korstockscan-low-price-two-leg@sk_eternix_midday.service
  korstockscan-low-price-two-leg-preflight@samsung_heavy_midday.service
  korstockscan-low-price-two-leg-preflight@samsung_heavy_afternoon.service
  korstockscan-low-price-two-leg-preflight@daewoo_ec_midday.service
  korstockscan-low-price-two-leg-preflight@daewoo_ec_afternoon.service
  korstockscan-low-price-two-leg-preflight@sk_eternix_midday.service
)
FILES=(
  korstockscan-low-price-two-leg@.service
  korstockscan-low-price-two-leg-preflight@.service
  "${TIMERS[@]}"
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

/bin/systemctl disable --now "${TIMERS[@]}" 2>/dev/null || true
/bin/systemctl stop "${SERVICES[@]}" 2>/dev/null || true
for unit in "${FILES[@]}"; do
  /bin/rm -f "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload

echo "removed only lower-price two-leg units; state, authority, and held-position records were preserved"
