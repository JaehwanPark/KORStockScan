# HOLD/EXIT Sentinel 2026-06-19

## 판정

- primary: `RUNTIME_OPS`
- secondary: `HOLD_DEFER_DANGER, AI_HOLDING_OPS, SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `holding_runtime_ops_playbook`
- followup_owner: `operator_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-06-19T12:40:02`
- exit_signal unique: `60`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `60` / `1` / `1`
- sell_sent/exit_signal: `1.7%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `1.7%`
- flow defer events: `114`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `88.5%`
- trailing missed-upside: `35.3%`
- top reasons: `AI보유감시:cache_miss=664, flow유예:scalp_trailing_take_profit=81, 청산신호:scalp_trailing_take_profit=66, soft_stop_grace=56, flow유예:scalp_soft_stop_pct=33`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check holding pipeline event freshness; restart only after explicit approval.
