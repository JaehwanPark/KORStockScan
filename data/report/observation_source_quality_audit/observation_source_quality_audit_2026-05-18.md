# Observation Source Quality Audit - 2026-05-18

- status: `warning`
- event_count: `1619996`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `blocked_strength_momentum` sample=`346539` missing=`{'metric_role': 1.0, 'decision_authority': 1.0, 'runtime_effect': 1.0, 'forbidden_uses': 1.0, 'threshold_family': 1.0, 'gate_action': 1.0, 'allowed_runtime_apply': 1.0, 'actual_order_submitted': 1.0}` zero=`{}`
- `blocked_overbought` sample=`77587` missing=`{'metric_role': 1.0, 'decision_authority': 1.0, 'runtime_effect': 1.0, 'forbidden_uses': 1.0, 'threshold_family': 1.0, 'gate_action': 1.0, 'allowed_runtime_apply': 1.0, 'actual_order_submitted': 1.0}` zero=`{'distance_from_day_high_pct': 0.265}`
- `blocked_liquidity` sample=`7438` missing=`{'threshold_family': 1.0, 'gate_action': 1.0, 'allowed_runtime_apply': 1.0, 'actual_order_submitted': 1.0}` zero=`{}`
- `ai_holding_fast_reuse_band` sample=`230` missing=`{'metric_role': 1.0, 'decision_authority': 1.0, 'runtime_effect': 1.0, 'forbidden_uses': 1.0, 'source_quality_route': 1.0}` zero=`{}`
- `soft_stop_expert_shadow` sample=`79` missing=`{'metric_role': 1.0, 'decision_authority': 1.0, 'runtime_effect': 1.0, 'forbidden_uses': 1.0, 'source_quality_route': 1.0}` zero=`{}`
- `holding_flow_override_candidate_cleared` sample=`59` missing=`{'metric_role': 1.0, 'decision_authority': 1.0, 'runtime_effect': 1.0, 'forbidden_uses': 1.0, 'source_quality_route': 1.0}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `blocked_swing_score_vpw`: `666194`
- `strength_momentum_observed`: `346539`
- `blocked_strength_momentum`: `346539`
- `blocked_swing_gap`: `139697`
- `blocked_overbought`: `77587`
- `swing_probe_discarded`: `17469`
- `strength_momentum_pass`: `8397`
- `blocked_liquidity`: `7438`
- `dynamic_vpw_override_pass`: `3724`
- `blocked_ai_score`: `834`
- `ai_confirmed`: `643`
- `stat_action_decision_snapshot`: `512`
- `bad_entry_refined_candidate`: `488`
- `swing_reentry_counterfactual_after_loss`: `453`
- `holding_flow_override_defer_exit`: `334`
- `ai_holding_fast_reuse_band`: `230`
- `ai_holding_reuse_bypass`: `216`
- `ai_holding_review`: `216`
- `reversal_add_blocked_reason`: `188`
- `soft_stop_micro_grace`: `176`
