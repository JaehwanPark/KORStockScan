# HOLD/EXIT Sentinel 2026-07-31

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW, TRAILING_EARLY_EXIT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-07-31T15:30:01`
- exit_signal unique: `8`
- sell_order_sent unique: `5`
- sell_completed unique: `5`
- real exit/sell_sent/sell_completed: `5` / `5` / `5`
- non-real exit/sell_sent/sell_completed: `3` / `0` / `0`
- sell_sent/exit_signal: `62.5%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 101, 'legacy_or_unclassified_score50': 714, 'preflight_source_quality_blocked': 16}`
- score50 preflight/source-quality blocked: `16`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `94.1%`
- trailing missed-upside: `33.3%`
- top reasons: `AI보유감시:cache_miss=229, soft_stop_grace=11, 청산신호:scalp_trailing_take_profit=6, sell_order_sent=5, sell_completed=5`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
