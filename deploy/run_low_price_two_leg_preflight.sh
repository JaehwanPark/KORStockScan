#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
PROFILE="${1:-}"
TARGET_DATE="$(TZ=Asia/Seoul /bin/date +%F)"

case "$PROFILE" in
  lotte_chemical_midday|lx_semicon_morning|lotte_chemical_morning|lotte_chemical_afternoon) ;;
  samsung_heavy_midday|samsung_heavy_afternoon|sk_eternix_midday|mirae_asset_morning|hanwha_ocean_late_morning|kepco_afternoon|sk_eternix_morning|mirae_asset_midday|sk_eternix_afternoon|samsung_heavy_morning|samsung_ea_morning|samsung_ea_late_morning|samsung_ea_afternoon|kepco_late_morning|kepco_midday|sk_eternix_late_morning|mirae_asset_late_morning|kepco_morning|sd_biosensor_morning|sd_biosensor_late_morning|sd_biosensor_midday|samsung_ea_midday|fan_ocean_morning|fan_ocean_late_morning|samsung_heavy_late_morning|fan_ocean_afternoon|sd_biosensor_afternoon) ;;
  *)
    echo "unsupported low-price two-leg profile: $PROFILE" >&2
    exit 2
    ;;
esac

/usr/bin/mkdir -p "$PROJECT_DIR/data/runtime/low_price_two_leg"
PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
  src.engine.automation.low_price_two_leg_policy_apply \
  --target-date "$TARGET_DATE" \
  --write

for attempt in $(/usr/bin/seq 1 18); do
  if /usr/bin/tmux has-session -t bot 2>/dev/null; then
    if PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
      src.trading.low_price_two_leg.preflight \
      --profile "$PROFILE" \
      --target-date "$TARGET_DATE" \
      --main-bot-active \
      --write; then
      exit 0
    else
      preflight_rc=$?
    fi
    if [ "$preflight_rc" -eq 4 ]; then
      echo "low-price two-leg preflight terminal quarantine profile=$PROFILE" >&2
      exit 4
    fi
  else
    echo "preflight profile=$PROFILE attempt=$attempt main_bot_inactive"
  fi
  /bin/sleep 5
done

echo "low-price two-leg preflight failed profile=$PROFILE after 18 attempts" >&2
exit 2
