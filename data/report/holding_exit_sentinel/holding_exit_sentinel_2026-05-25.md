# HOLD/EXIT Sentinel 2026-05-25

## 판정

- primary: `RUNTIME_OPS`
- secondary: `SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `holding_runtime_ops_playbook`
- followup_owner: `operator_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-05-25T12:45:03`
- exit_signal unique: `0`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `0` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `0.0%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `31.6%`
- top reasons: `-`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check holding pipeline event freshness; restart only after explicit approval.
