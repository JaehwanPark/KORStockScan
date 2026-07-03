# HOLD/EXIT Sentinel 2026-07-03

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-07-03T10:45:03`
- exit_signal unique: `3`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `3` / `1` / `1`
- sell_sent/exit_signal: `33.3%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `33.3%`
- flow defer events: `1`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `87.5%`
- trailing missed-upside: `26.5%`
- top reasons: `AI보유감시:cache_miss=48, soft_stop_grace=16, 청산신호:scalp_soft_stop_pct=4, flow유예:scalp_soft_stop_pct=1, 청산신호:scalp_low_profit_stagnation_hard_exit=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
