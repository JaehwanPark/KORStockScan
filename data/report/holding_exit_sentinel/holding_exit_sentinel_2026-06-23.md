# HOLD/EXIT Sentinel 2026-06-23

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

- as_of: `2026-06-23T15:30:03`
- exit_signal unique: `61`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `61` / `1` / `1`
- sell_sent/exit_signal: `1.6%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `1.6%`
- flow defer events: `123`
- AI holding cache MISS: `99.9%`
- soft_stop rebound above sell 10m: `88.5%`
- trailing missed-upside: `34.3%`
- top reasons: `AI보유감시:cache_miss=703, soft_stop_grace=167, flow유예:scalp_soft_stop_pct=81, 청산신호:scalp_soft_stop_pct=61, 청산신호:scalp_hard_stop_pct=51`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
