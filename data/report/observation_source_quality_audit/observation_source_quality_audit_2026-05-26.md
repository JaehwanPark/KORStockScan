# Observation Source Quality Audit - 2026-05-26

- status: `warning`
- event_count: `470359`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `blocked_strength_momentum` sample=`32538` missing=`{}` zero=`{'intraday_range_pct': 0.154}`
- `blocked_overbought` sample=`20849` missing=`{}` zero=`{'intraday_range_pct': 0.2248}`
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`270` missing=`{'sim_overbought_risk_state': 0.8815}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`202` missing=`{'simulated_order': 0.1139}` zero=`{}`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- `initial_entry_qty_cap_applied` count=`317` routing=`instrumentation_gap_or_diagnostic_contract_needed`

## Top Stages
- `blocked_swing_score_vpw`: `187457`
- `strength_momentum_observed`: `32538`
- `blocked_strength_momentum`: `32538`
- `blocked_overbought`: `20849`
- `bad_entry_refined_candidate`: `20539`
- `scalp_sim_panic_scale_in_blocked`: `20387`
- `stat_action_decision_snapshot`: `16461`
- `blocked_swing_gap`: `13766`
- `scalp_sim_panic_action_deduped`: `8751`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `8446`
- `scalp_entry_action_decision_snapshot`: `8045`
- `swing_probe_discarded`: `8029`
- `reversal_add_blocked_reason`: `7475`
- `ai_holding_fast_reuse_band`: `7074`
- `ai_holding_reuse_bypass`: `7044`
- `holding_flow_override_defer_exit`: `5658`
- `ai_holding_review`: `4422`
- `scalp_sim_ai_holding_live_call`: `4234`
- `reversal_add_gate_blocked`: `3769`
- `pyramid_blocked_reason`: `3216`
