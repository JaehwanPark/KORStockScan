# HOLD/EXIT Sentinel 2026-08-04

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

- as_of: `2026-08-04T15:30:02`
- exit_signal unique: `19`
- sell_order_sent unique: `14`
- sell_completed unique: `14`
- real exit/sell_sent/sell_completed: `14` / `14` / `14`
- non-real exit/sell_sent/sell_completed: `5` / `0` / `0`
- sell_sent/exit_signal: `73.7%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 497, 'legacy_or_unclassified_score50': 3292, 'preflight_source_quality_blocked': 63}`
- score50 preflight/source-quality blocked: `63`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=1067, 청산신호:scalp_trailing_take_profit=397, soft_stop_grace=170, sell_order_sent=14, sell_completed=14`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
