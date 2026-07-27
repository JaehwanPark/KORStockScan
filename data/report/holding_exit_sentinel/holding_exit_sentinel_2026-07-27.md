# HOLD/EXIT Sentinel 2026-07-27

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

- as_of: `2026-07-27T14:50:02`
- exit_signal unique: `0`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `0` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 13, 'legacy_or_unclassified_score50': 64}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `96.6%`
- trailing missed-upside: `33.3%`
- top reasons: `AI보유감시:cache_miss=13`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically.
