# HOLD/EXIT Sentinel 2026-07-07

## 판정

- primary: `HOLD_DEFER_DANGER`
- secondary: `AI_HOLDING_OPS, SOFT_STOP_WHIPSAW`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `holding_flow_defer_cost_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-07-07T14:25:06`
- exit_signal unique: `20`
- sell_order_sent unique: `9`
- sell_completed unique: `9`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `20` / `9` / `9`
- sell_sent/exit_signal: `45.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `45.0%`
- flow defer events: `76`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'legacy_or_unclassified_score50': 1536, 'not_called_neutral_unusable': 3, 'post_call_source_quality_neutralized': 169}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `169`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `25.5%`
- top reasons: `AI보유감시:cache_miss=505, flow유예:scalp_soft_stop_pct=76, soft_stop_grace=71, 청산신호:scalp_soft_stop_pct=23, sell_order_sent=9`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
