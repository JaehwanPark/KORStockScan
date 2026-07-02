# HOLD/EXIT Sentinel 2026-07-02

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

- as_of: `2026-07-02T11:10:01`
- exit_signal unique: `6`
- sell_order_sent unique: `2`
- sell_completed unique: `2`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `6` / `2` / `2`
- sell_sent/exit_signal: `33.3%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `33.3%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=99, 청산신호:scalp_soft_stop_pct=5, 청산신호:scalp_trailing_take_profit=3, 청산신호:scalp_low_profit_stagnation_hard_exit=2, sell_order_sent=2`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
