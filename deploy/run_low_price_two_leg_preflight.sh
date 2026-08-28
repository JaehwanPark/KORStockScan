#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ubuntu/KORStockScan"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
PROFILE="${1:-}"
TARGET_DATE="$(/bin/date +%F)"

case "$PROFILE" in
  samsung_heavy_midday|samsung_heavy_afternoon|sk_eternix_midday|mirae_asset_morning|jeju_semiconductor_morning|doosan_enerbility_morning|hanwha_ocean_late_morning|kakao_morning|kepco_afternoon|kakao_late_morning|sk_eternix_morning|mirae_asset_midday|sk_eternix_afternoon|samsung_heavy_morning|doosan_enerbility_late_morning|kakao_midday|sk_telecom_afternoon|samsung_ea_morning|samsung_ea_late_morning|samsung_ea_afternoon|sk_telecom_late_morning|sk_telecom_morning|hanse_morning|hanse_afternoon|cj_cgv_midday|cj_cgv_afternoon|tym_midday|tym_afternoon|cj_cgv_late_morning|kepco_late_morning|kepco_midday|hanse_late_morning|hanse_midday|nhn_afternoon|youngone_morning|youngone_afternoon|sk_eternix_late_morning|mirae_asset_late_morning|kepco_morning|nhn_morning|nhn_late_morning|sd_biosensor_morning|sd_biosensor_late_morning|sd_biosensor_midday|doosan_enerbility_afternoon|samsung_ea_midday|fan_ocean_morning|fan_ocean_late_morning) ;;
  *)
    echo "unsupported low-price two-leg profile: $PROFILE" >&2
    exit 2
    ;;
esac

/usr/bin/mkdir -p "$PROJECT_DIR/data/runtime/low_price_two_leg"
exec 9>"$PROJECT_DIR/data/runtime/low_price_two_leg/policy_apply.lock"
/usr/bin/flock -w 30 9
PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
  src.engine.automation.low_price_two_leg_policy_apply \
  --target-date "$TARGET_DATE" \
  --write
/usr/bin/flock -u 9

for attempt in $(/usr/bin/seq 1 18); do
  if /usr/bin/tmux has-session -t bot 2>/dev/null; then
    if PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" -m \
      src.trading.low_price_two_leg.preflight \
      --profile "$PROFILE" \
      --target-date "$TARGET_DATE" \
      --main-bot-active \
      --write; then
      exit 0
    fi
  else
    echo "preflight profile=$PROFILE attempt=$attempt main_bot_inactive"
  fi
  /bin/sleep 5
done

echo "low-price two-leg preflight failed profile=$PROFILE after 18 attempts" >&2
exit 2
