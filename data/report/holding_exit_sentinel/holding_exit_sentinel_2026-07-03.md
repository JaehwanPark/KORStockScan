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

- as_of: `2026-07-03T15:30:02`
- exit_signal unique: `16`
- sell_order_sent unique: `11`
- sell_completed unique: `11`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `16` / `11` / `11`
- sell_sent/exit_signal: `68.8%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `68.8%`
- flow defer events: `4`
- AI holding cache MISS: `99.9%`
- soft_stop rebound above sell 10m: `87.5%`
- trailing missed-upside: `26.5%`
- top reasons: `AI보유감시:cache_miss=822, soft_stop_grace=42, sell_order_sent=11, sell_completed=11, 청산신호:scalp_soft_stop_pct=9`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
