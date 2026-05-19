# Observation Source Quality Audit - 2026-05-19

- status: `warning`
- event_count: `477812`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `ai_confirmed` sample=`1703` missing=`{'tick_source_quality_fields_sent': 0.249, 'tick_accel_source': 0.249, 'tick_context_quality': 0.249, 'quote_age_source': 0.249}` zero=`{}`
- `blocked_strength_momentum` sample=`50152` missing=`{}` zero=`{'distance_from_day_high_pct': 0.3547}`
- `blocked_overbought` sample=`18107` missing=`{}` zero=`{'distance_from_day_high_pct': 0.9475}`
- `scale_in_price_resolved` sample=`19` missing=`{'orderbook_micro_snapshot_age_ms': 0.4211}` zero=`{}`
- `scale_in_price_p2_observe` sample=`19` missing=`{'orderbook_micro_snapshot_age_ms': 0.4211}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- `loss_fallback_probe` count=`5424` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `soft_stop_whipsaw_confirmation` count=`123` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `entry_armed` count=`72` routing=`instrumentation_gap_or_diagnostic_contract_needed`
- `entry_armed_expired_after_wait` count=`69` routing=`instrumentation_gap_or_diagnostic_contract_needed`

## Top Stages
- `blocked_swing_score_vpw`: `255951`
- `strength_momentum_observed`: `50152`
- `blocked_strength_momentum`: `50152`
- `blocked_overbought`: `18107`
- `blocked_swing_gap`: `14396`
- `bad_entry_refined_candidate`: `9917`
- `stat_action_decision_snapshot`: `8938`
- `swing_probe_discarded`: `7431`
- `holding_flow_override_force_exit`: `5448`
- `loss_fallback_probe`: `5424`
- `ai_holding_fast_reuse_band`: `4283`
- `ai_holding_reuse_bypass`: `4184`
- `ai_holding_review`: `4148`
- `scalp_entry_action_decision_snapshot`: `4108`
- `reversal_add_blocked_reason`: `4042`
- `holding_flow_override_defer_exit`: `3523`
- `reversal_add_gate_blocked`: `3197`
- `blocked_ai_score`: `2761`
- `blocked_vpw`: `2134`
- `scalp_sim_ai_holding_live_call`: `1753`
