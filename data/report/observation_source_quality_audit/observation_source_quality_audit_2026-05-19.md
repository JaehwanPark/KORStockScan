# Observation Source Quality Audit - 2026-05-19

- status: `warning`
- event_count: `508946`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `loss_fallback_probe` sample=`8064` missing=`{'fallback_reason': 1.0}` zero=`{}`
- `soft_stop_whipsaw_confirmation` sample=`123` missing=`{'flow_state': 1.0}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `blocked_swing_score_vpw`: `279693`
- `strength_momentum_observed`: `50152`
- `blocked_strength_momentum`: `50152`
- `blocked_overbought`: `18107`
- `blocked_swing_gap`: `14396`
- `bad_entry_refined_candidate`: `10545`
- `stat_action_decision_snapshot`: `9168`
- `holding_flow_override_force_exit`: `8088`
- `loss_fallback_probe`: `8064`
- `swing_probe_discarded`: `7864`
- `ai_holding_fast_reuse_band`: `4283`
- `ai_holding_reuse_bypass`: `4184`
- `ai_holding_review`: `4148`
- `scalp_entry_action_decision_snapshot`: `4108`
- `reversal_add_blocked_reason`: `4042`
- `holding_flow_override_defer_exit`: `3523`
- `reversal_add_gate_blocked`: `3432`
- `blocked_ai_score`: `2761`
- `blocked_vpw`: `2134`
- `scalp_sim_ai_holding_live_call`: `1753`
