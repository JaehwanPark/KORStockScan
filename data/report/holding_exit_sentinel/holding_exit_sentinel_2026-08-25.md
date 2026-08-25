# HOLD/EXIT Sentinel 2026-08-25

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

- as_of: `2026-08-25T12:00:03`
- exit_signal unique: `15`
- sell_order_sent unique: `6`
- sell_completed unique: `6`
- real exit/sell_sent/sell_completed: `6` / `6` / `6`
- non-real exit/sell_sent/sell_completed: `9` / `0` / `0`
- sell_sent/exit_signal: `40.0%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `0`
- non-real flow defer/force/confirm: `0` / `5` / `3`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 75, 'legacy_or_unclassified_score50': 982, 'not_called_neutral_unusable': 2, 'post_call_source_quality_neutralized': 65, 'preflight_source_quality_blocked': 35}`
- score50 preflight/source-quality blocked: `85`
- score50 raw-non50 neutralized: `65`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=280, soft_stop_grace=120, 청산신호:scalp_trailing_take_profit=8, sell_order_sent=6, sell_completed=6`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
