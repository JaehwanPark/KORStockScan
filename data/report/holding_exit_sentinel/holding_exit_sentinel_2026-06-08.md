# HOLD/EXIT Sentinel 2026-06-08

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

- as_of: `2026-06-08T11:50:04`
- exit_signal unique: `83`
- sell_order_sent unique: `8`
- sell_completed unique: `8`
- real exit/sell_sent/sell_completed: `8` / `8` / `8`
- non-real exit/sell_sent/sell_completed: `75` / `0` / `0`
- sell_sent/exit_signal: `9.6%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `572`
- AI holding cache MISS: `99.8%`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=2052, flow유예:scalp_trailing_take_profit=314, flow유예:scalp_soft_stop_pct=258, soft_stop_grace=237, 청산신호:scalp_hard_stop_pct=79`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
