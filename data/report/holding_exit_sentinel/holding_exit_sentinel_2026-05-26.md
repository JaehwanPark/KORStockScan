# HOLD/EXIT Sentinel 2026-05-26

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

- as_of: `2026-05-26T15:30:04`
- exit_signal unique: `110`
- sell_order_sent unique: `7`
- sell_completed unique: `7`
- real exit/sell_sent/sell_completed: `7` / `7` / `7`
- non-real exit/sell_sent/sell_completed: `103` / `0` / `0`
- sell_sent/exit_signal: `6.4%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `5658`
- AI holding cache MISS: `99.7%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `30.0%`
- top reasons: `AI보유감시:cache_miss=4409, flow유예:scalp_trailing_take_profit=3313, flow유예:scalp_soft_stop_pct=2345, soft_stop_grace=1931, 청산신호:scalp_trailing_take_profit=70`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
