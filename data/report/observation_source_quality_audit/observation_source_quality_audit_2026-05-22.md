# Observation Source Quality Audit - 2026-05-22

- status: `warning`
- event_count: `397285`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_sim_sell_order_assumed_filled` sample=`123` missing=`{'simulated_order': 0.1626}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `blocked_swing_score_vpw`: `80953`
- `strength_momentum_observed`: `60920`
- `blocked_strength_momentum`: `60920`
- `blocked_swing_gap`: `58064`
- `blocked_overbought`: `24884`
- `bad_entry_refined_candidate`: `14191`
- `scalp_sim_panic_scale_in_blocked`: `13107`
- `stat_action_decision_snapshot`: `11783`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `9540`
- `scalp_sim_panic_action_deduped`: `5829`
- `reversal_add_gate_blocked`: `4299`
- `reversal_add_blocked_reason`: `4278`
- `ai_holding_fast_reuse_band`: `4075`
- `ai_holding_reuse_bypass`: `4065`
- `swing_probe_discarded`: `3914`
- `scalp_entry_action_decision_snapshot`: `3713`
- `holding_flow_override_defer_exit`: `3425`
- `scalp_sim_ai_holding_live_call`: `2848`
- `ai_holding_review`: `2848`
- `pyramid_blocked_reason`: `2784`
