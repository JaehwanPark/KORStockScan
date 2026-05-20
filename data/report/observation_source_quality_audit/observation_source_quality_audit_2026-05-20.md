# Observation Source Quality Audit - 2026-05-20

- status: `warning`
- event_count: `593358`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `loss_fallback_probe` sample=`90` missing=`{'fallback_reason': 0.5333}` zero=`{}`
- `soft_stop_whipsaw_confirmation` sample=`83` missing=`{'flow_state': 1.0}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `blocked_swing_score_vpw`: `368504`
- `scalp_sim_panic_action_deduped`: `47298`
- `strength_momentum_observed`: `40970`
- `blocked_strength_momentum`: `40970`
- `blocked_overbought`: `18403`
- `swing_probe_discarded`: `9216`
- `stat_action_decision_snapshot`: `8549`
- `bad_entry_refined_candidate`: `6336`
- `scalp_sim_panic_scale_in_blocked`: `4783`
- `scalp_entry_action_decision_snapshot`: `4508`
- `holding_flow_override_defer_exit`: `4323`
- `blocked_ai_score`: `2815`
- `reversal_add_blocked_reason`: `2478`
- `ai_holding_fast_reuse_band`: `2470`
- `ai_holding_reuse_bypass`: `2469`
- `blocked_vpw`: `2334`
- `ai_confirmed`: `1857`
- `scalp_sim_ai_holding_live_call`: `1754`
- `ai_holding_review`: `1754`
- `scale_in_qty_block`: `1509`
