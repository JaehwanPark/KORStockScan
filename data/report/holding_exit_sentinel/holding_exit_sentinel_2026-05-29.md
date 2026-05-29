# HOLD/EXIT Sentinel 2026-05-29

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

- as_of: `2026-05-29T15:05:05`
- exit_signal unique: `93`
- sell_order_sent unique: `4`
- sell_completed unique: `4`
- real exit/sell_sent/sell_completed: `4` / `4` / `4`
- non-real exit/sell_sent/sell_completed: `89` / `0` / `0`
- sell_sent/exit_signal: `4.3%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `3313`
- AI holding cache MISS: `99.6%`
- soft_stop rebound above sell 10m: `91.7%`
- trailing missed-upside: `29.2%`
- top reasons: `AI보유감시:cache_miss=2429, flow유예:scalp_trailing_take_profit=2425, flow유예:scalp_soft_stop_pct=869, soft_stop_grace=555, 청산신호:scalp_trailing_take_profit=81`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
