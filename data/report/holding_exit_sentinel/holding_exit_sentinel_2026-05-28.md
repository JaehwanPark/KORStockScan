# HOLD/EXIT Sentinel 2026-05-28

## 판정

- primary: `SELL_EXECUTION_DROUGHT`
- secondary: `HOLD_DEFER_DANGER, AI_HOLDING_OPS, SOFT_STOP_WHIPSAW`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `sell_receipt_order_path_check`
- followup_owner: `postclose_holding_exit_attribution`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-28T15:30:03`
- exit_signal unique: `100`
- sell_order_sent unique: `0`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `3` / `0` / `1`
- non-real exit/sell_sent/sell_completed: `97` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `2848`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `91.3%`
- trailing missed-upside: `29.2%`
- top reasons: `AI보유감시:cache_miss=2965, flow유예:scalp_trailing_take_profit=1654, flow유예:scalp_soft_stop_pct=1194, soft_stop_grace=924, 청산신호:scalp_soft_stop_pct=375`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check sell order receipt/order path before changing exit thresholds.
