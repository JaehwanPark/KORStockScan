# HOLD/EXIT Sentinel 2026-05-27

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

- as_of: `2026-05-27T15:30:04`
- exit_signal unique: `90`
- sell_order_sent unique: `5`
- sell_completed unique: `5`
- real exit/sell_sent/sell_completed: `5` / `5` / `5`
- non-real exit/sell_sent/sell_completed: `85` / `0` / `0`
- sell_sent/exit_signal: `5.6%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `3337`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `30.4%`
- top reasons: `AI보유감시:cache_miss=4250, flow유예:scalp_soft_stop_pct=1677, flow유예:scalp_trailing_take_profit=1634, soft_stop_grace=1496, 청산신호:scalp_hard_stop_pct=70`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
