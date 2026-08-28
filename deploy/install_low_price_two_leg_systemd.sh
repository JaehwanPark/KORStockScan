#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
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
  korstockscan-low-price-two-leg-sk-telecom-morning-preflight.timer
  korstockscan-low-price-two-leg-sk-telecom-morning.timer
  korstockscan-low-price-two-leg-hanse-morning-preflight.timer
  korstockscan-low-price-two-leg-hanse-morning.timer
  korstockscan-low-price-two-leg-hanse-afternoon-preflight.timer
  korstockscan-low-price-two-leg-hanse-afternoon.timer
  korstockscan-low-price-two-leg-cj-cgv-midday-preflight.timer
  korstockscan-low-price-two-leg-cj-cgv-midday.timer
  korstockscan-low-price-two-leg-cj-cgv-afternoon-preflight.timer
  korstockscan-low-price-two-leg-cj-cgv-afternoon.timer
  korstockscan-low-price-two-leg-tym-midday-preflight.timer
  korstockscan-low-price-two-leg-tym-midday.timer
  korstockscan-low-price-two-leg-tym-afternoon-preflight.timer
  korstockscan-low-price-two-leg-tym-afternoon.timer
  korstockscan-low-price-two-leg-cj-cgv-late-morning-preflight.timer
  korstockscan-low-price-two-leg-cj-cgv-late-morning.timer
  korstockscan-low-price-two-leg-kepco-late-morning-preflight.timer
  korstockscan-low-price-two-leg-kepco-late-morning.timer
  korstockscan-low-price-two-leg-kepco-midday-preflight.timer
  korstockscan-low-price-two-leg-kepco-midday.timer
  korstockscan-low-price-two-leg-hanse-late-morning-preflight.timer
  korstockscan-low-price-two-leg-hanse-late-morning.timer
  korstockscan-low-price-two-leg-hanse-midday-preflight.timer
  korstockscan-low-price-two-leg-hanse-midday.timer
  korstockscan-low-price-two-leg-nhn-afternoon-preflight.timer
  korstockscan-low-price-two-leg-nhn-afternoon.timer
  korstockscan-low-price-two-leg-youngone-morning-preflight.timer
  korstockscan-low-price-two-leg-youngone-morning.timer
  korstockscan-low-price-two-leg-youngone-afternoon-preflight.timer
  korstockscan-low-price-two-leg-youngone-afternoon.timer
  korstockscan-low-price-two-leg-sk-eternix-late-morning-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-late-morning.timer
  korstockscan-low-price-two-leg-mirae-asset-late-morning-preflight.timer
  korstockscan-low-price-two-leg-mirae-asset-late-morning.timer
  korstockscan-low-price-two-leg-kepco-morning-preflight.timer
  korstockscan-low-price-two-leg-kepco-morning.timer
  korstockscan-low-price-two-leg-nhn-morning-preflight.timer
  korstockscan-low-price-two-leg-nhn-morning.timer
  korstockscan-low-price-two-leg-nhn-late-morning-preflight.timer
  korstockscan-low-price-two-leg-nhn-late-morning.timer
  korstockscan-low-price-two-leg-sd-biosensor-morning-preflight.timer
  korstockscan-low-price-two-leg-sd-biosensor-morning.timer
  korstockscan-low-price-two-leg-sd-biosensor-late-morning-preflight.timer
  korstockscan-low-price-two-leg-sd-biosensor-late-morning.timer
  korstockscan-low-price-two-leg-sd-biosensor-midday-preflight.timer
  korstockscan-low-price-two-leg-sd-biosensor-midday.timer
  korstockscan-low-price-two-leg-doosan-enerbility-afternoon-preflight.timer
  korstockscan-low-price-two-leg-doosan-enerbility-afternoon.timer
  korstockscan-low-price-two-leg-samsung-ea-midday-preflight.timer
  korstockscan-low-price-two-leg-samsung-ea-midday.timer
  korstockscan-low-price-two-leg-fan-ocean-morning-preflight.timer
  korstockscan-low-price-two-leg-fan-ocean-morning.timer
  korstockscan-low-price-two-leg-fan-ocean-late-morning-preflight.timer
  korstockscan-low-price-two-leg-fan-ocean-late-morning.timer
)
TIMERS=(
  korstockscan-low-price-two-leg-samsung-heavy-midday-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-midday.timer
  korstockscan-low-price-two-leg-samsung-heavy-afternoon-preflight.timer
  korstockscan-low-price-two-leg-samsung-heavy-afternoon.timer
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
  korstockscan-low-price-two-leg-sk-telecom-morning-preflight.timer
  korstockscan-low-price-two-leg-sk-telecom-morning.timer
  korstockscan-low-price-two-leg-hanse-morning-preflight.timer
  korstockscan-low-price-two-leg-hanse-morning.timer
  korstockscan-low-price-two-leg-hanse-afternoon-preflight.timer
  korstockscan-low-price-two-leg-hanse-afternoon.timer
  korstockscan-low-price-two-leg-cj-cgv-midday-preflight.timer
  korstockscan-low-price-two-leg-cj-cgv-midday.timer
  korstockscan-low-price-two-leg-cj-cgv-afternoon-preflight.timer
  korstockscan-low-price-two-leg-cj-cgv-afternoon.timer
  korstockscan-low-price-two-leg-tym-midday-preflight.timer
  korstockscan-low-price-two-leg-tym-midday.timer
  korstockscan-low-price-two-leg-tym-afternoon-preflight.timer
  korstockscan-low-price-two-leg-tym-afternoon.timer
  korstockscan-low-price-two-leg-cj-cgv-late-morning-preflight.timer
  korstockscan-low-price-two-leg-cj-cgv-late-morning.timer
  korstockscan-low-price-two-leg-kepco-late-morning-preflight.timer
  korstockscan-low-price-two-leg-kepco-late-morning.timer
  korstockscan-low-price-two-leg-kepco-midday-preflight.timer
  korstockscan-low-price-two-leg-kepco-midday.timer
  korstockscan-low-price-two-leg-hanse-late-morning-preflight.timer
  korstockscan-low-price-two-leg-hanse-late-morning.timer
  korstockscan-low-price-two-leg-hanse-midday-preflight.timer
  korstockscan-low-price-two-leg-hanse-midday.timer
  korstockscan-low-price-two-leg-nhn-afternoon-preflight.timer
  korstockscan-low-price-two-leg-nhn-afternoon.timer
  korstockscan-low-price-two-leg-youngone-morning-preflight.timer
  korstockscan-low-price-two-leg-youngone-morning.timer
  korstockscan-low-price-two-leg-youngone-afternoon-preflight.timer
  korstockscan-low-price-two-leg-youngone-afternoon.timer
  korstockscan-low-price-two-leg-sk-eternix-late-morning-preflight.timer
  korstockscan-low-price-two-leg-sk-eternix-late-morning.timer
  korstockscan-low-price-two-leg-mirae-asset-late-morning-preflight.timer
  korstockscan-low-price-two-leg-mirae-asset-late-morning.timer
  korstockscan-low-price-two-leg-kepco-morning-preflight.timer
  korstockscan-low-price-two-leg-kepco-morning.timer
  korstockscan-low-price-two-leg-nhn-morning-preflight.timer
  korstockscan-low-price-two-leg-nhn-morning.timer
  korstockscan-low-price-two-leg-nhn-late-morning-preflight.timer
  korstockscan-low-price-two-leg-nhn-late-morning.timer
  korstockscan-low-price-two-leg-sd-biosensor-morning-preflight.timer
  korstockscan-low-price-two-leg-sd-biosensor-morning.timer
  korstockscan-low-price-two-leg-sd-biosensor-late-morning-preflight.timer
  korstockscan-low-price-two-leg-sd-biosensor-late-morning.timer
  korstockscan-low-price-two-leg-sd-biosensor-midday-preflight.timer
  korstockscan-low-price-two-leg-sd-biosensor-midday.timer
  korstockscan-low-price-two-leg-doosan-enerbility-afternoon-preflight.timer
  korstockscan-low-price-two-leg-doosan-enerbility-afternoon.timer
  korstockscan-low-price-two-leg-samsung-ea-midday-preflight.timer
  korstockscan-low-price-two-leg-samsung-ea-midday.timer
  korstockscan-low-price-two-leg-fan-ocean-morning-preflight.timer
  korstockscan-low-price-two-leg-fan-ocean-morning.timer
  korstockscan-low-price-two-leg-fan-ocean-late-morning-preflight.timer
  korstockscan-low-price-two-leg-fan-ocean-late-morning.timer
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
PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" - <<'PY'
from src.engine.risk.manual_control_exclusion import (
    add_manual_control_exclusion_code,
    manual_control_operator_exclusion_source,
)

owners = {
    "006800": "mirae_asset_low_price_two_leg_owner",
    "035720": "kakao_low_price_two_leg_owner",
    "015760": "kepco_low_price_two_leg_owner",
    "017670": "sk_telecom_low_price_two_leg_owner",
    "028050": "samsung_ea_low_price_two_leg_owner",
    "028670": "fan_ocean_low_price_two_leg_owner",
    "105630": "hanse_low_price_two_leg_owner",
    "079160": "cj_cgv_low_price_two_leg_owner",
    "002900": "tym_low_price_two_leg_owner",
    "111770": "youngone_low_price_two_leg_owner",
    "137310": "sd_biosensor_low_price_two_leg_owner",
    "181710": "nhn_low_price_two_leg_owner",
    "475150": "sk_eternix_low_price_two_leg_owner",
}
for code, owner in owners.items():
    add_manual_control_exclusion_code(code, comment=f"manual_operator {owner}")
    if manual_control_operator_exclusion_source(code) != "manual_operator":
        raise SystemExit(f"failed to activate low-price manual owner for {code}")
PY
/bin/systemctl enable --now "${TIMERS[@]}"
/bin/systemctl list-timers --all --no-pager "${TIMERS[@]}"

echo "installed forty-eight lower-price profile timers; retired Daewoo units were removed"
