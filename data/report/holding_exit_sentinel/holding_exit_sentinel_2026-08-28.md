# HOLD/EXIT Sentinel 2026-08-28

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

- as_of: `2026-08-28T15:30:03`
- exit_signal unique: `10`
- sell_order_sent unique: `3`
- sell_completed unique: `3`
- real exit/sell_sent/sell_completed: `3` / `3` / `3`
- non-real exit/sell_sent/sell_completed: `7` / `0` / `0`
- sell_sent/exit_signal: `30.0%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `1`
- non-real flow defer/force/confirm: `0` / `2` / `1`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 76, 'legacy_or_unclassified_score50': 1413, 'post_call_source_quality_neutralized': 125, 'preflight_source_quality_blocked': 20}`
- score50 preflight/source-quality blocked: `77`
- score50 raw-non50 neutralized: `125`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=344, soft_stop_grace=49, 청산신호:scalp_preset_hard_stop_pct=5, 청산신호:scalp_trailing_take_profit=4, sell_order_sent=3`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
