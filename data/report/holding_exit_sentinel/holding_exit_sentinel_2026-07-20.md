# HOLD/EXIT Sentinel 2026-07-20

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

- as_of: `2026-07-20T15:30:02`
- exit_signal unique: `23`
- sell_order_sent unique: `14`
- sell_completed unique: `14`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `23` / `14` / `14`
- sell_sent/exit_signal: `60.9%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `60.9%`
- flow defer events: `4`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 2, 'legacy_or_unclassified_score50': 833, 'post_call_source_quality_neutralized': 96, 'preflight_source_quality_blocked': 65}`
- score50 preflight/source-quality blocked: `65`
- score50 raw-non50 neutralized: `96`
- soft_stop rebound above sell 10m: `95.8%`
- trailing missed-upside: `31.9%`
- top reasons: `AI보유감시:cache_miss=365, 청산신호:scalp_trailing_take_profit=18, sell_order_sent=14, sell_completed=14, soft_stop_grace=13`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
