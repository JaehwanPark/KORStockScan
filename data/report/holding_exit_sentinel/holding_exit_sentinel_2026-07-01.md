# HOLD/EXIT Sentinel 2026-07-01

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-07-01T15:30:02`
- exit_signal unique: `37`
- sell_order_sent unique: `25`
- sell_completed unique: `25`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `37` / `25` / `25`
- sell_sent/exit_signal: `67.6%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `67.6%`
- flow defer events: `8`
- AI holding cache MISS: `99.5%`
- soft_stop rebound above sell 10m: `66.7%`
- trailing missed-upside: `37.5%`
- top reasons: `AI보유감시:cache_miss=1761, soft_stop_grace=37, 청산신호:scalp_ai_momentum_decay=34, 청산신호:scalp_trailing_take_profit=31, sell_order_sent=26`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
