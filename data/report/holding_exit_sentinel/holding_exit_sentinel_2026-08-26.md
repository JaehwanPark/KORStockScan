# HOLD/EXIT Sentinel 2026-08-26

## 판정

- primary: `AI_HOLDING_OPS`
- secondary: `SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `ai_holding_provenance_review`
- followup_owner: `runtime_stability_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-08-26T15:30:02`
- exit_signal unique: `8`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `8` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `0`
- non-real flow defer/force/confirm: `0` / `4` / `3`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 118, 'legacy_or_unclassified_score50': 2848, 'post_call_source_quality_neutralized': 284, 'preflight_source_quality_blocked': 37}`
- score50 preflight/source-quality blocked: `139`
- score50 raw-non50 neutralized: `284`
- soft_stop rebound above sell 10m: `100.0%`
- trailing missed-upside: `33.9%`
- top reasons: `AI보유감시:cache_miss=635, soft_stop_grace=126, 청산신호:scalp_trailing_take_profit=4, 청산신호:scalp_preset_hard_stop_pct=4, 청산신호:scalp_soft_stop_pct=3`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
