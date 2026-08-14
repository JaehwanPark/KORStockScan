# HOLD/EXIT Sentinel 2026-08-14

## 판정

- primary: `RUNTIME_OPS`
- secondary: `HOLD_DEFER_DANGER, AI_HOLDING_OPS`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `true`
- followup_route: `holding_runtime_ops_playbook`
- followup_owner: `operator_review`
- runtime_effect: `report_only_no_mutation`

## 근거

- as_of: `2026-08-14T11:30:02`
- exit_signal unique: `6`
- sell_order_sent unique: `2`
- sell_completed unique: `1`
- real exit/sell_sent/sell_completed: `2` / `2` / `1`
- non-real exit/sell_sent/sell_completed: `4` / `0` / `0`
- sell_sent/exit_signal: `33.3%`
- real sell_sent/exit_signal: `100.0%`
- non-real sell_sent/exit_signal: `0.0%`
- flow defer events: `0`
- AI holding cache MISS: `100.0%`
- score50 origins: `{'fallback_score_50': 13, 'legacy_or_unclassified_score50': 538, 'preflight_source_quality_blocked': 3}`
- score50 preflight/source-quality blocked: `3`
- score50 raw-non50 neutralized: `0`
- soft_stop rebound above sell 10m: `0.0%`
- trailing missed-upside: `0.0%`
- top reasons: `AI보유감시:cache_miss=92, 청산신호:scalp_trailing_take_profit=57, soft_stop_grace=32, 청산신호:scalp_preset_hard_stop_pct=3, sell_order_sent=2`

## 금지된 자동변경

- `auto_sell`
- `holding_threshold_relaxation`
- `holding_flow_override_mutation`
- `ai_cache_ttl_mutation`
- `bot_restart`

## 권고 액션

- Check holding pipeline event freshness; restart only after explicit approval.
