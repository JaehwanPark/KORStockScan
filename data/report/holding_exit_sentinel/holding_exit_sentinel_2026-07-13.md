# HOLD/EXIT Sentinel 2026-07-13

## 판정

- primary: `NORMAL`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `normal_no_action`
- followup_owner: `none`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-07-13T10:10:01`
- exit_signal unique: `2`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `2` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'legacy_or_unclassified_score50': 7}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=3, 청산신호:scalp_preset_hard_stop_pct=2`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Continue monitoring; no dynamic action required.
