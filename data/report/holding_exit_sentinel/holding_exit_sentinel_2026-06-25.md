# HOLD/EXIT Sentinel 2026-06-25

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

- as_of: `2026-06-25T15:30:02`
- exit_signal unique: `27`
- sell_order_sent unique: `2`
- sell_completed unique: `2`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `27` / `2` / `2`
- sell_sent/exit_signal: `7.4%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `7.4%`
- flow defer events: `12`
- AI holding cache MISS: `99.8%`
- soft_stop rebound above sell 10m: `89.3%`
- trailing missed-upside: `36.1%`
- top reasons: `AI보유감시:cache_miss=479, soft_stop_grace=52, 청산신호:scalp_soft_stop_pct=30, 청산신호:scalp_hard_stop_pct=13, 청산신호:scalp_trailing_take_profit=7`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
