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
  korstockscan-low-price-two-leg-sk-eternix-midday-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-midday.timer
)
TIMERS=(
  korstockscan-low-price-two-leg-samsung-heavy-midday-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-midday.timer
  korstockscan-low-price-two-leg-samsung-heavy-afternoon-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-afternoon.timer
  korstockscan-low-price-two-leg-sk-eternix-midday-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-midday.timer
)
RETIRED_DAEWOO_UNITS=(
  korstockscan-low-price-two-leg-daewoo-ec-midday-preflight.timer
  korstockscan-low-price-two-leg-daewoo-ec-midday.timer
  korstockscan-low-price-two-leg-daewoo-ec-afternoon-preflight.timer
  korstockscan-low-price-two-leg-daewoo-ec-afternoon.timer
)
RETIRED_DAEWOO_SERVICES=(
  korstockscan-low-price-two-leg@daewoo_ec_midday.service
  korstockscan-low-price-two-leg@daewoo_ec_afternoon.service
  korstockscan-low-price-two-leg-preflight@daewoo_ec_midday.service
  korstockscan-low-price-two-leg-preflight@daewoo_ec_afternoon.service
)

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

/bin/systemd-analyze verify "${UNITS[@]/#/$SYSTEMD_DIR/}"
/usr/bin/test -x "$SCRIPT_DIR/run_low_price_two_leg_preflight.sh"
/usr/bin/test -x "$SCRIPT_DIR/run_low_price_two_leg_live.sh"
/bin/systemctl disable --now "${RETIRED_DAEWOO_UNITS[@]}" 2>/dev/null || true
/bin/systemctl stop "${RETIRED_DAEWOO_SERVICES[@]}" 2>/dev/null || true
for unit in "${RETIRED_DAEWOO_UNITS[@]}"; do
  /bin/rm -f "$TARGET_DIR/$unit"
done
for unit in "${UNITS[@]}"; do
  /usr/bin/install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done
/bin/systemctl daemon-reload
/bin/systemctl enable --now "${TIMERS[@]}"
/bin/systemctl list-timers --all --no-pager "${TIMERS[@]}"

echo "installed three lower-price profile timers; retired Daewoo units were removed"
