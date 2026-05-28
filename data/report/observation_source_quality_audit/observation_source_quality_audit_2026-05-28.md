# Observation Source Quality Audit - 2026-05-28

- status: `warning`
- event_count: `265387`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`199` missing=`{'sim_overbought_risk_state': 0.9648}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`200` missing=`{'simulated_order': 0.08}` zero=`{}`
- `swing_same_symbol_loss_reentry_cooldown` sample=`7` missing=`{'source_probe_id': 0.2857}` zero=`{}`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `budget_pass`: `20926`
- `orderbook_stability_observed`: `20919`
- `latency_block`: `20789`
- `swing_entry_policy_evaluated`: `19675`
- `swing_entry_micro_context_observed`: `19580`
- `market_regime_block`: `14954`
- `blocked_swing_score_vpw`: `14364`
- `bad_entry_refined_candidate`: `10950`
- `scalp_sim_panic_scale_in_blocked`: `9880`
- `stat_action_decision_snapshot`: `8429`
- `strength_momentum_observed`: `7340`
- `blocked_strength_momentum`: `7340`
- `blocked_gatekeeper_reject`: `5311`
- `market_regime_prior_observed`: `4721`
- `gatekeeper_fast_reuse_bypass`: `4677`
- `scalp_entry_action_decision_snapshot`: `4454`
- `gatekeeper_reject_cache_reuse`: `4295`
- `reversal_add_blocked_reason`: `4271`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `4242`
- `scalp_sim_panic_action_deduped`: `4184`
