# HOLD/EXIT Sentinel 2026-07-13

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

- as_of: `2026-07-13T12:15:03`
- exit_signal unique: `7`
- sell_order_sent unique: `1`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `7` / `1` / `1`
- sell_sent/exit_signal: `14.3%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `14.3%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'legacy_or_unclassified_score50': 606, 'post_call_source_quality_neutralized': 47}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `47`
- soft_stop rebound above sell 10m: `95.2%`
- trailing missed-upside: `29.5%`
- top reasons: `AI보유감시:cache_miss=194, soft_stop_grace=45, 청산신호:scalp_soft_stop_pct=4, 청산신호:scalp_preset_hard_stop_pct=2, 청산신호:scalp_low_profit_stagnation_hard_exit=1`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
