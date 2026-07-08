# HOLD/EXIT Sentinel 2026-07-08

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

- as_of: `2026-07-08T10:00:02`
- exit_signal unique: `5`
- sell_order_sent unique: `4`
- sell_completed unique: `4`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `5` / `4` / `4`
- sell_sent/exit_signal: `80.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `80.0%`
- flow defer events: `40`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 1, 'legacy_or_unclassified_score50': 153, 'post_call_source_quality_neutralized': 18}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `18`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=102, soft_stop_grace=53, flow유예:scalp_soft_stop_pct=40, 청산신호:scalp_soft_stop_pct=10, sell_order_sent=4`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
