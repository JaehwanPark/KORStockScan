# HOLD/EXIT Sentinel 2026-07-10

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

- as_of: `2026-07-10T15:30:03`
- exit_signal unique: `16`
- sell_order_sent unique: `9`
- sell_completed unique: `9`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `16` / `9` / `9`
- sell_sent/exit_signal: `56.2%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `56.2%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 1, 'legacy_or_unclassified_score50': 1761, 'not_called_neutral_unusable': 4, 'post_call_source_quality_neutralized': 224}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `224`
- soft_stop rebound above sell 10m: `94.4%`
- trailing missed-upside: `31.6%`
- top reasons: `AI보유감시:cache_miss=547, 청산신호:scalp_trailing_take_profit=9, sell_order_sent=9, sell_completed=9, 청산신호:scalp_soft_stop_pct=3`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
