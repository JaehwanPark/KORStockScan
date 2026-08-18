# HOLD/EXIT Sentinel 2026-08-18

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

- as_of: `2026-08-18T11:00:02`
- exit_signal unique: `10`
- sell_order_sent unique: `3`
- sell_completed unique: `3`
- real exit/sell_sent/sell_completed: `3` / `3` / `3`
- non-real exit/sell_sent/sell_completed: `7` / `0` / `0`
- sell_sent/exit_signal: `30.0%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 35, 'legacy_or_unclassified_score50': 485, 'post_call_source_quality_neutralized': 33, 'preflight_source_quality_blocked': 18}`
- score50 preflight/source-quality blocked: `18`
- score50 raw-non50 neutralized: `33`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=159, soft_stop_grace=80, 청산신호:scalp_trailing_take_profit=58, sell_order_sent=3, sell_completed=3`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
