# HOLD/EXIT Sentinel 2026-08-24

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

- as_of: `2026-08-24T15:30:02`
- exit_signal unique: `21`
- sell_order_sent unique: `6`
- sell_completed unique: `6`
- real exit/sell_sent/sell_completed: `6` / `6` / `6`
- non-real exit/sell_sent/sell_completed: `15` / `0` / `0`
- sell_sent/exit_signal: `28.6%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- real flow defer/force/confirm: `0` / `0` / `2`
- non-real flow defer/force/confirm: `0` / `13` / `1`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 194, 'legacy_or_unclassified_score50': 2957, 'post_call_source_quality_neutralized': 258, 'preflight_source_quality_blocked': 117}`
- score50 preflight/source-quality blocked: `244`
- score50 raw-non50 neutralized: `258`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=823, soft_stop_grace=75, 청산신호:scalp_trailing_take_profit=15, sell_order_sent=6, sell_completed=6`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
