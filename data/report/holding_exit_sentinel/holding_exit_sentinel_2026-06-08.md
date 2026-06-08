# HOLD/EXIT Sentinel 2026-06-08

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

- as_of: `2026-06-08T15:30:06`
- exit_signal unique: `125`
- sell_order_sent unique: `22`
- sell_completed unique: `25`
- real exit/sell_sent/sell_completed: `22` / `22` / `25`
- non-real exit/sell_sent/sell_completed: `103` / `0` / `0`
- sell_sent/exit_signal: `17.6%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `1459`
- AI holding cache MISS: `99.9%`
- soft_stop rebound above sell 10m: `72.7%`
- trailing missed-upside: `40.0%`
- top reasons: `AI보유감시:cache_miss=5210, flow유예:scalp_soft_stop_pct=835, soft_stop_grace=708, flow유예:scalp_trailing_take_profit=621, 청산신호:scalp_hard_stop_pct=147`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
