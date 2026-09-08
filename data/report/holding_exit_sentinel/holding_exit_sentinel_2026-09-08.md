# HOLD/EXIT Sentinel 2026-09-08

## 판정

- primary: `RUNTIME_OPS`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `holding_runtime_ops_playbook`
- followup_owner: `operator_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-09-08T09:15:02`
- exit_signal unique: `0`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `0` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `0`
- non-real flow defer/force/confirm: `0` / `0` / `0`
- AI holding cache MISS: `0.0%`
- score50 origins: `{}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `-`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check holding pipeline event freshness; restart only after explicit approval.
