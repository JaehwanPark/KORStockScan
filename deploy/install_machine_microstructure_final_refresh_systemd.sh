#!/usr/bin/env bash

set -euo pipefail

if ((EUID != 0)); then
  printf 'run as root: sudo %s\n' "$0" >&2
  exit 1
fi

PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
UNIT_SOURCE_DIR="$PROJECT_DIR/deploy/systemd"
UNIT_INSTALL_DIR="/etc/systemd/system"
TIMER_STATE_DIR="/var/lib/systemd/timers"
OLD_BASE="korstockscan-widget-expansion-recommendation"
NEW_BASE="korstockscan-machine-microstructure-final-refresh"
OLD_TIMER="$OLD_BASE.timer"
NEW_TIMER="$NEW_BASE.timer"
OLD_STAMP="$TIMER_STATE_DIR/stamp-$OLD_TIMER"
NEW_STAMP="$TIMER_STATE_DIR/stamp-$NEW_TIMER"

systemd-analyze verify \
  "$UNIT_SOURCE_DIR/$NEW_BASE.service" \
  "$UNIT_SOURCE_DIR/$NEW_TIMER"
install -m 0644 "$UNIT_SOURCE_DIR/$NEW_BASE.service" "$UNIT_INSTALL_DIR/$NEW_BASE.service"
install -m 0644 "$UNIT_SOURCE_DIR/$NEW_TIMER" "$UNIT_INSTALL_DIR/$NEW_TIMER"

# Preserve an existing new-owner stamp on idempotent re-runs. On the first
# migration, inherit the old owner's last trigger (or use now when no old
# owner exists) so Persistent=true cannot interpret deployment as a missed run.
if [[ ! -e "$NEW_STAMP" ]]; then
  install -m 0644 /dev/null "$NEW_STAMP"
  if [[ -e "$OLD_STAMP" ]]; then
    touch -r "$OLD_STAMP" "$NEW_STAMP"
  fi
fi

systemctl daemon-reload
systemctl enable "$NEW_TIMER"
systemctl stop "$OLD_TIMER" 2>/dev/null || true
if ! systemctl start "$NEW_TIMER"; then
  systemctl disable --now "$NEW_TIMER" 2>/dev/null || true
  systemctl start "$OLD_TIMER" 2>/dev/null || true
  printf 'failed to activate %s; restored %s\n' "$NEW_TIMER" "$OLD_TIMER" >&2
  exit 1
fi
if ! systemctl is-enabled --quiet "$NEW_TIMER" || ! systemctl is-active --quiet "$NEW_TIMER"; then
  systemctl disable --now "$NEW_TIMER" 2>/dev/null || true
  systemctl start "$OLD_TIMER" 2>/dev/null || true
  printf 'verification failed for %s; restored %s\n' "$NEW_TIMER" "$OLD_TIMER" >&2
  exit 1
fi
next_elapse="$(systemctl show "$NEW_TIMER" --property=NextElapseUSecRealtime --value)"
if [[ -z "$next_elapse" || "$next_elapse" == "n/a" ]]; then
  systemctl disable --now "$NEW_TIMER" 2>/dev/null || true
  systemctl start "$OLD_TIMER" 2>/dev/null || true
  printf 'next schedule verification failed for %s; restored %s\n' "$NEW_TIMER" "$OLD_TIMER" >&2
  exit 1
fi
cmp -s "$UNIT_SOURCE_DIR/$NEW_BASE.service" "$UNIT_INSTALL_DIR/$NEW_BASE.service"
cmp -s "$UNIT_SOURCE_DIR/$NEW_TIMER" "$UNIT_INSTALL_DIR/$NEW_TIMER"

systemctl disable "$OLD_TIMER" 2>/dev/null || true
rm -f \
  "$UNIT_INSTALL_DIR/$OLD_BASE.service" \
  "$UNIT_INSTALL_DIR/$OLD_TIMER" \
  "$OLD_STAMP"
systemctl daemon-reload

printf '[MACHINE_MICRO_SYSTEMD] timer=%s enabled=true active=true old_timer_removed=true next=%s\n' \
  "$NEW_TIMER" "$next_elapse"
