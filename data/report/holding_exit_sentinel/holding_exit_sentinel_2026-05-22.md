# HOLD/EXIT Sentinel 2026-05-22

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-22T15:30:03`
- exit_signal unique: `92`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `92` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `3425`
- AI holding cache MISS: `99.8%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `31.6%`
- top reasons: `AI보유감시:cache_miss=2842, flow유예:scalp_trailing_take_profit=2041, flow유예:scalp_soft_stop_pct=1212, soft_stop_grace=1174, flow유예:scalp_ai_momentum_decay=172`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
