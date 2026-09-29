#!/usr/bin/env bash
set -euo pipefail

# Release cutover helper. Run only after the selected release has the gateway
# RETIRED_NEW_BUY guard and broker/owner custody was independently reconciled.
PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
source "$PROJECT_DIR/deploy/runtime_release_set_lock.sh"
if [[ "${1:-}" != "--apply" ]]; then
  echo "usage: sudo $0 --apply (after broker/owner flat custody review)" >&2
  exit 2
fi
if [[ "$EUID" -ne 0 ]]; then
  echo "root required to disable systemd timers" >&2
  exit 2
fi
runtime_release_set_lock_acquire "$PROJECT_DIR"

PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" - "$PROJECT_DIR" <<'PY'
import json
import sys
from pathlib import Path
from src.engine.infrastructure.runtime_release_router import selected_release

workspace = Path(sys.argv[1])
root = workspace / "data/runtime"
release, _commit = selected_release(workspace)
for segment in ("samsung_morning_one_share", "samsung_midday_one_share", "samsung_afternoon_one_share"):
    gateway = release / "src/trading" / segment / "gateway.py"
    if not gateway.is_file() or "RETIRED_NEW_BUY" not in gateway.read_text(encoding="utf-8"):
        raise SystemExit(f"retirement blocked: selected gateway not retired: {segment}")
names = (
    "samsung_morning_one_share_state.json",
    "samsung_morning_sor_reentry_state.json",
    "samsung_midday_one_share_state.json",
    "samsung_afternoon_one_share_state.json",
    "samsung_morning_manual_addon_2026-08-13.json",
)
safe = {"READY", "NO_TRADE", "NO_FILL", "COMPLETE"}
for name in names:
    path = root / name
    if not path.exists():
        raise SystemExit(f"retirement blocked by missing state: {name}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise ValueError("invalid_state")
        if name.startswith("samsung_morning_manual_addon"):
            legs = state.get("legs") or {}
            if (state.get("status") != "NO_FILL"
                or int(state.get("total_filled_quantity") or 0) != 0
                or int(state.get("manual_sell_required_quantity") or 0) != 0
                or not isinstance(legs, dict)
                or any(not isinstance(leg, dict)
                       or int(leg.get("filled_quantity") or 0) != 0
                       or any(not isinstance(attempt, dict)
                              or int(attempt.get("remaining_quantity") or 0) != 0
                              or attempt.get("status") not in {"CLOSED", "REJECTED"}
                              for attempt in (leg.get("attempts") or {}).values())
                       for leg in legs.values())):
                raise ValueError("manual_addon_custody_not_terminal")
            continue
        legs = state.get("legs") or []
        if (str(state.get("status") or "") not in safe
            or int(state.get("position_qty") or 0) != 0
            or state.get("pending_entry_confirmation")
            or state.get("owner_registry_reconciliation_required")
            or not isinstance(legs, list)
            or any(not isinstance(leg, dict)
                   or str(leg.get("status") or "") not in safe
                   or int(leg.get("position_qty") or 0) != 0
                   for leg in legs)):
            raise ValueError("custody_not_flat_or_terminal")
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"retirement blocked by {name}: {exc}")
PY

services=(
  korstockscan-samsung-morning-one-share.service
  korstockscan-samsung-midday-one-share.service
  korstockscan-samsung-afternoon-one-share.service
  korstockscan-samsung-morning-manual-addon-20260813.service
)
for unit in "${services[@]}"; do
  if /bin/systemctl is-active --quiet "$unit"; then
    echo "retirement blocked: active custody service $unit" >&2
    exit 3
  fi
done

timers=(
  korstockscan-samsung-morning-one-share.timer
  korstockscan-samsung-one-share-preflight.timer
  korstockscan-samsung-midday-one-share.timer
  korstockscan-samsung-midday-one-share-preflight.timer
  korstockscan-samsung-afternoon-one-share.timer
  korstockscan-samsung-afternoon-one-share-preflight.timer
  korstockscan-samsung-morning-manual-addon-20260813.timer
)
for unit in "${timers[@]}"; do
  if /bin/systemctl cat "$unit" >/dev/null 2>&1; then
    /bin/systemctl disable --now "$unit"
    if /bin/systemctl is-enabled --quiet "$unit" || /bin/systemctl is-active --quiet "$unit"; then
      echo "retirement blocked: timer remains enabled or active $unit" >&2
      exit 4
    fi
  fi
done
/bin/systemctl list-timers --all --no-pager "${timers[@]}"
