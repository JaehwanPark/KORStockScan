# HOLD/EXIT Sentinel 2026-07-07

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

- as_of: `2026-07-07T11:40:02`
- exit_signal unique: `11`
- sell_order_sent unique: `4`
- sell_completed unique: `4`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `11` / `4` / `4`
- sell_sent/exit_signal: `36.4%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `36.4%`
- flow defer events: `71`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'legacy_or_unclassified_score50': 649, 'not_called_neutral_unusable': 1, 'post_call_source_quality_neutralized': 42}`
- score50 preflight/source-quality blocked: `0`
- score50 raw-non50 neutralized: `42`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=258, flow유예:scalp_soft_stop_pct=71, soft_stop_grace=60, 청산신호:scalp_soft_stop_pct=19, 청산신호:scalp_trailing_take_profit=6`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
