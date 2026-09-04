# HOLD/EXIT Sentinel 2026-09-04

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

- as_of: `2026-09-04T19:20:02`
- exit_signal unique: `3`
- sell_order_sent unique: `2`
- sell_completed unique: `2`
- real exit/sell_sent/sell_completed: `1` / `2` / `2`
- non-real exit/sell_sent/sell_completed: `2` / `0` / `0`
- sell_sent/exit_signal: `66.7%`
- real sell_sent/exit_signal: `200.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `0`
- non-real flow defer/force/confirm: `0` / `0` / `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 70, 'legacy_or_unclassified_score50': 681, 'not_called_neutral_unusable': 1, 'post_call_source_quality_neutralized': 12, 'preflight_source_quality_blocked': 23}`
- score50 preflight/source-quality blocked: `93`
- score50 raw-non50 neutralized: `12`
- soft_stop rebound above sell 10m: `100.0%`
- trailing missed-upside: `60.0%`
- top reasons: `AI보유감시:cache_miss=115, sell_order_sent=2, sell_completed=2, 청산신호:scalp_preset_hard_stop_pct=2, 청산신호:scalp_trailing_take_profit=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
