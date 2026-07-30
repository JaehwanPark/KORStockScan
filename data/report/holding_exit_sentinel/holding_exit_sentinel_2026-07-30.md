# HOLD/EXIT Sentinel 2026-07-30

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

- as_of: `2026-07-30T15:30:03`
- exit_signal unique: `3`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `1` / `1` / `1`
- non-real exit/sell_sent/sell_completed: `2` / `0` / `0`
- sell_sent/exit_signal: `33.3%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 12, 'legacy_or_unclassified_score50': 77}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `94.1%`
- trailing missed-upside: `32.7%`
- top reasons: `청산신호:scalp_soft_stop_pct=19, AI보유감시:cache_miss=12, sell_order_sent=1, sell_completed=1, 청산신호:scalp_trailing_take_profit=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
