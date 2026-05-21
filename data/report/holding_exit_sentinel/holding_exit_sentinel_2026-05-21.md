# HOLD/EXIT Sentinel 2026-05-21

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-21T10:05:02`
- exit_signal unique: `45`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `45` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `1276`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `flow유예:scalp_trailing_take_profit=956, AI보유감시:cache_miss=501, flow유예:scalp_soft_stop_pct=315, soft_stop_grace=314, 청산신호:scalp_trailing_take_profit=19`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
