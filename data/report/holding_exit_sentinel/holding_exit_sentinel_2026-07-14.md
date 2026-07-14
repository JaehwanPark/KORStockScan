# HOLD/EXIT Sentinel 2026-07-14

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

- as_of: `2026-07-14T15:30:03`
- exit_signal unique: `2`
- sell_order_sent unique: `2`
- sell_completed unique: `2`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `2` / `2` / `2`
- sell_sent/exit_signal: `100.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `100.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 1, 'legacy_or_unclassified_score50': 843, 'not_called_neutral_unusable': 1, 'post_call_source_quality_neutralized': 81}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `81`
- soft_stop rebound above sell 10m: `95.5%`
- trailing missed-upside: `30.6%`
- top reasons: `AI보유감시:cache_miss=226, 청산신호:scalp_trailing_take_profit=2, sell_order_sent=2, sell_completed=2, soft_stop_grace=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
