# HOLD/EXIT Sentinel 2026-06-05

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

- as_of: `2026-06-05T12:50:04`
- exit_signal unique: `45`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `1` / `1` / `1`
- non-real exit/sell_sent/sell_completed: `44` / `0` / `0`
- sell_sent/exit_signal: `2.2%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `1133`
- AI holding cache MISS: `99.9%`
- soft_stop rebound above sell 10m: `72.7%`
- trailing missed-upside: `38.9%`
- top reasons: `AI보유감시:cache_miss=1123, flow유예:scalp_soft_stop_pct=697, soft_stop_grace=560, flow유예:scalp_trailing_take_profit=436, 청산신호:scalp_soft_stop_pct=23`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
