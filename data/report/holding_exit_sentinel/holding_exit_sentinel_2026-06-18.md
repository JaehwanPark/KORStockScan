# HOLD/EXIT Sentinel 2026-06-18

## 판정

- primary: `SELL_EXECUTION_DROUGHT`
- secondary: `HOLD_DEFER_DANGER, AI_HOLDING_OPS, SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `sell_receipt_order_path_check`
- followup_owner: `postclose_holding_exit_attribution`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-06-18T15:30:06`
- exit_signal unique: `124`
- sell_order_sent unique: `8`
- sell_completed unique: `8`
- real exit/sell_sent/sell_completed: `9` / `8` / `8`
- non-real exit/sell_sent/sell_completed: `115` / `0` / `0`
- sell_sent/exit_signal: `6.5%`
- real sell_sent/exit_signal: `88.9%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `2105`
- AI holding cache MISS: `99.9%`
- soft_stop rebound above sell 10m: `88.5%`
- trailing missed-upside: `36.4%`
- top reasons: `AI보유감시:cache_miss=3877, soft_stop_grace=1850, flow유예:scalp_soft_stop_pct=1148, flow유예:scalp_trailing_take_profit=950, 청산신호:scalp_soft_stop_pct=84`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check sell order receipt/order path before changing exit thresholds.
