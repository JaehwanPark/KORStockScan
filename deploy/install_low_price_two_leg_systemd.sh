#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-low-price-two-leg@.service
  korstockscan-low-price-two-leg-preflight@.service
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

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

/bin/systemd-analyze verify "${UNITS[@]/#/$SYSTEMD_DIR/}"
/usr/bin/test -x "$SCRIPT_DIR/run_low_price_two_leg_preflight.sh"
/usr/bin/test -x "$SCRIPT_DIR/run_low_price_two_leg_live.sh"
for unit in "${UNITS[@]}"; do
  /usr/bin/install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload
/bin/systemctl enable --now "${TIMERS[@]}"
/bin/systemctl list-timers --all --no-pager "${TIMERS[@]}"

echo "installed five lower-price profile timers; existing Samsung and widget units were not changed"
