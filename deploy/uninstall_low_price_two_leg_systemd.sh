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
  korstockscan-low-price-two-leg-mirae-asset-morning-preflight.timer
  korstockscan-low-price-two-leg-mirae-asset-morning.timer
  korstockscan-low-price-two-leg-jeju-semiconductor-morning-preflight.timer
  korstockscan-low-price-two-leg-jeju-semiconductor-morning.timer
  korstockscan-low-price-two-leg-doosan-enerbility-morning-preflight.timer
  korstockscan-low-price-two-leg-doosan-enerbility-morning.timer
  korstockscan-low-price-two-leg-hanwha-ocean-late-morning-preflight.timer
  korstockscan-low-price-two-leg-hanwha-ocean-late-morning.timer
  korstockscan-low-price-two-leg-kakao-morning-preflight.timer
  korstockscan-low-price-two-leg-kakao-morning.timer
  korstockscan-low-price-two-leg-kepco-afternoon-preflight.timer
  korstockscan-low-price-two-leg-kepco-afternoon.timer
  korstockscan-low-price-two-leg-kakao-late-morning-preflight.timer
  korstockscan-low-price-two-leg-kakao-late-morning.timer
  korstockscan-low-price-two-leg-sk-eternix-morning-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-morning.timer
  korstockscan-low-price-two-leg-mirae-asset-midday-preflight.timer
  korstockscan-low-price-two-leg-mirae-asset-midday.timer
  korstockscan-low-price-two-leg-sk-eternix-afternoon-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-afternoon.timer
  korstockscan-low-price-two-leg-samsung-heavy-morning-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-morning.timer
  korstockscan-low-price-two-leg-doosan-enerbility-late-morning-preflight.timer
  korstockscan-low-price-two-leg-doosan-enerbility-late-morning.timer
  korstockscan-low-price-two-leg-kakao-midday-preflight.timer
  korstockscan-low-price-two-leg-kakao-midday.timer
  korstockscan-low-price-two-leg-sk-telecom-afternoon-preflight.timer
  korstockscan-low-price-two-leg-sk-telecom-afternoon.timer
  korstockscan-low-price-two-leg-samsung-ea-morning-preflight.timer
  korstockscan-low-price-two-leg-samsung-ea-morning.timer
  korstockscan-low-price-two-leg-samsung-ea-late-morning-preflight.timer
  korstockscan-low-price-two-leg-samsung-ea-late-morning.timer
  korstockscan-low-price-two-leg-samsung-ea-afternoon-preflight.timer
  korstockscan-low-price-two-leg-samsung-ea-afternoon.timer
  korstockscan-low-price-two-leg-sk-telecom-late-morning-preflight.timer
  korstockscan-low-price-two-leg-sk-telecom-late-morning.timer
  korstockscan-low-price-two-leg-hanse-morning-preflight.timer
  korstockscan-low-price-two-leg-hanse-morning.timer
  korstockscan-low-price-two-leg-hanse-afternoon-preflight.timer
  korstockscan-low-price-two-leg-hanse-afternoon.timer
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
  korstockscan-low-price-two-leg@mirae_asset_morning.service
  korstockscan-low-price-two-leg@jeju_semiconductor_morning.service
  korstockscan-low-price-two-leg@doosan_enerbility_morning.service
  korstockscan-low-price-two-leg@hanwha_ocean_late_morning.service
  korstockscan-low-price-two-leg-preflight@mirae_asset_morning.service
  korstockscan-low-price-two-leg-preflight@jeju_semiconductor_morning.service
  korstockscan-low-price-two-leg-preflight@doosan_enerbility_morning.service
  korstockscan-low-price-two-leg-preflight@hanwha_ocean_late_morning.service
  korstockscan-low-price-two-leg@kakao_morning.service
  korstockscan-low-price-two-leg@kepco_afternoon.service
  korstockscan-low-price-two-leg@kakao_late_morning.service
  korstockscan-low-price-two-leg@sk_eternix_morning.service
  korstockscan-low-price-two-leg@mirae_asset_midday.service
  korstockscan-low-price-two-leg@sk_eternix_afternoon.service
  korstockscan-low-price-two-leg-preflight@kakao_morning.service
  korstockscan-low-price-two-leg-preflight@kepco_afternoon.service
  korstockscan-low-price-two-leg-preflight@kakao_late_morning.service
  korstockscan-low-price-two-leg-preflight@sk_eternix_morning.service
  korstockscan-low-price-two-leg-preflight@mirae_asset_midday.service
  korstockscan-low-price-two-leg-preflight@sk_eternix_afternoon.service
  korstockscan-low-price-two-leg@samsung_heavy_morning.service
  korstockscan-low-price-two-leg@doosan_enerbility_late_morning.service
  korstockscan-low-price-two-leg@kakao_midday.service
  korstockscan-low-price-two-leg@sk_telecom_afternoon.service
  korstockscan-low-price-two-leg@samsung_ea_morning.service
  korstockscan-low-price-two-leg@samsung_ea_late_morning.service
  korstockscan-low-price-two-leg@samsung_ea_afternoon.service
  korstockscan-low-price-two-leg-preflight@samsung_heavy_morning.service
  korstockscan-low-price-two-leg-preflight@doosan_enerbility_late_morning.service
  korstockscan-low-price-two-leg-preflight@kakao_midday.service
  korstockscan-low-price-two-leg-preflight@sk_telecom_afternoon.service
  korstockscan-low-price-two-leg-preflight@samsung_ea_morning.service
  korstockscan-low-price-two-leg-preflight@samsung_ea_late_morning.service
  korstockscan-low-price-two-leg-preflight@samsung_ea_afternoon.service
  korstockscan-low-price-two-leg@sk_telecom_late_morning.service
  korstockscan-low-price-two-leg-preflight@sk_telecom_late_morning.service
  korstockscan-low-price-two-leg@hanse_morning.service
  korstockscan-low-price-two-leg-preflight@hanse_morning.service
  korstockscan-low-price-two-leg@hanse_afternoon.service
  korstockscan-low-price-two-leg-preflight@hanse_afternoon.service
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
