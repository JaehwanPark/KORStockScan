# HOLD/EXIT Sentinel 2026-08-31

## 판정

- primary: `AI_HOLDING_OPS`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `ai_holding_provenance_review`
- followup_owner: `runtime_stability_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-08-31T13:45:03`
- exit_signal unique: `7`
- sell_order_sent unique: `2`
- sell_completed unique: `2`
- real exit/sell_sent/sell_completed: `2` / `2` / `2`
- non-real exit/sell_sent/sell_completed: `5` / `0` / `0`
- sell_sent/exit_signal: `28.6%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `0`
- non-real flow defer/force/confirm: `0` / `3` / `2`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 28, 'legacy_or_unclassified_score50': 539, 'post_call_source_quality_neutralized': 25, 'preflight_source_quality_blocked': 17}`
- score50 preflight/source-quality blocked: `38`
- score50 raw-non50 neutralized: `25`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=110, soft_stop_grace=56, 청산신호:scalp_trailing_take_profit=5, sell_order_sent=2, sell_completed=2`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
