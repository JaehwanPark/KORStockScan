# HOLD/EXIT Sentinel 2026-07-02

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

- as_of: `2026-07-02T12:30:03`
- exit_signal unique: `11`
- sell_order_sent unique: `6`
- sell_completed unique: `6`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `11` / `6` / `6`
- sell_sent/exit_signal: `54.5%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `54.5%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `75.0%`
- trailing missed-upside: `33.3%`
- top reasons: `AI보유감시:cache_miss=364, 청산신호:scalp_soft_stop_pct=7, sell_order_sent=6, sell_completed=6, soft_stop_grace=6`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
