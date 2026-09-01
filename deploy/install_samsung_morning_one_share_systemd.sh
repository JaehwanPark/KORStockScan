#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
TARGET_DIR="/etc/systemd/system"
UNITS=(
  korstockscan-samsung-one-share-preflight.service
  korstockscan-samsung-morning-one-share.service
  korstockscan-samsung-morning-one-share.timer
)
LEGACY_PREFLIGHT_TIMER="korstockscan-samsung-one-share-preflight.timer"

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 2
fi

/bin/systemd-analyze verify "${UNITS[@]/#/$SYSTEMD_DIR/}"
for unit in "${UNITS[@]}"; do
  /usr/bin/install -m 0644 "$SYSTEMD_DIR/$unit" "$TARGET_DIR/$unit"
done

/bin/systemctl disable --now "$LEGACY_PREFLIGHT_TIMER" 2>/dev/null || true
/usr/bin/rm -f "$TARGET_DIR/$LEGACY_PREFLIGHT_TIMER"

/bin/systemctl daemon-reload

for service_unit in \
  korstockscan-samsung-one-share-preflight.service \
  korstockscan-samsung-morning-one-share.service; do
  installed_user="$(/bin/systemctl show "$service_unit" --property=User --value)"
  installed_group="$(/bin/systemctl show "$service_unit" --property=Group --value)"
  if [[ "$installed_user" != "ubuntu" || "$installed_group" != "ubuntu" ]]; then
    echo "installed credential contract mismatch unit=$service_unit user=$installed_user group=$installed_group" >&2
    exit 1
  fi
done

/bin/systemctl enable --now korstockscan-samsung-morning-one-share.timer

/bin/systemctl list-timers --all --no-pager \
  korstockscan-samsung-morning-one-share.timer

echo "installed single 07:57 machine timer with preflight dependency; widget service was not changed or restarted"
