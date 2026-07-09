# HOLD/EXIT Sentinel 2026-07-09

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

- as_of: `2026-07-09T15:30:02`
- exit_signal unique: `12`
- sell_order_sent unique: `5`
- sell_completed unique: `5`
- real exit/sell_sent/sell_completed: `1` / `1` / `1`
- non-real exit/sell_sent/sell_completed: `11` / `4` / `4`
- sell_sent/exit_signal: `41.7%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `36.4%`
- flow defer events: `2`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 3, 'legacy_or_unclassified_score50': 797, 'not_called_neutral_unusable': 1, 'post_call_source_quality_neutralized': 46}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `46`
- soft_stop rebound above sell 10m: `94.4%`
- trailing missed-upside: `32.1%`
- top reasons: `AI보유감시:cache_miss=296, soft_stop_grace=10, 청산신호:scalp_trailing_take_profit=5, sell_order_sent=5, sell_completed=5`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
