# HOLD/EXIT Sentinel 2026-05-18

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

- as_of: `2026-05-18T12:55:01`
- exit_signal unique: `29`
- sell_order_sent unique: `0`
- sell_completed unique: `0`
- real exit/sell_sent/sell_completed: `0` / `0` / `0`
- non-real exit/sell_sent/sell_completed: `29` / `0` / `0`
- sell_sent/exit_signal: `0.0%`
- real sell_sent/exit_signal: `0.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `12`
- AI holding cache MISS: `100.0%`
- soft_stop rebound above sell 10m: `90.9%`
- trailing missed-upside: `27.8%`
- top reasons: `AI보유감시:cache_miss=81, 청산신호:kospi_regime_stop_loss=20, 청산신호:kospi_trailing_start_take_profit=15, soft_stop_grace=15, flow유예:scalp_soft_stop_pct=11`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Review holding_flow_override defer examples and worsen floor evidence.
