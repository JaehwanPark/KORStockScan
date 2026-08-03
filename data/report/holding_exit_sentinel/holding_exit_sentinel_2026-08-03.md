# HOLD/EXIT Sentinel 2026-08-03

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-08-03T15:30:02`
- exit_signal unique: `10`
- sell_order_sent unique: `8`
- sell_completed unique: `8`
- real exit/sell_sent/sell_completed: `8` / `8` / `8`
- non-real exit/sell_sent/sell_completed: `2` / `0` / `0`
- sell_sent/exit_signal: `80.0%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 175, 'legacy_or_unclassified_score50': 1713, 'preflight_source_quality_blocked': 207}`
- score50 preflight/source-quality blocked: `207`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=587, soft_stop_grace=36, 청산신호:scalp_trailing_take_profit=27, sell_order_sent=8, sell_completed=8`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
