# Observation Source Quality Audit - 2026-05-28

- status: `warning`
- event_count: `210661`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`183` missing=`{'sim_overbought_risk_state': 0.9617}` zero=`{}`
- `swing_same_symbol_loss_reentry_cooldown` sample=`5` missing=`{'source_probe_id': 0.4}` zero=`{}`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `budget_pass`: `15508`
- `orderbook_stability_observed`: `15503`
- `latency_block`: `15392`
- `swing_entry_policy_evaluated`: `14260`
- `swing_entry_micro_context_observed`: `14194`
- `market_regime_block`: `10383`
- `blocked_swing_score_vpw`: `10296`
- `bad_entry_refined_candidate`: `9630`
- `scalp_sim_panic_scale_in_blocked`: `8882`
- `stat_action_decision_snapshot`: `7352`
- `strength_momentum_observed`: `6245`
- `blocked_strength_momentum`: `6245`
- `scalp_entry_action_decision_snapshot`: `4214`
- `blocked_gatekeeper_reject`: `3964`
- `reversal_add_blocked_reason`: `3882`
- `market_regime_prior_observed`: `3877`
- `scalp_sim_panic_action_deduped`: `3623`
- `gatekeeper_fast_reuse_bypass`: `3501`
- `ai_holding_fast_reuse_band`: `3489`
- `ai_holding_reuse_bypass`: `3472`
