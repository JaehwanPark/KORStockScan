# Observation Source Quality Audit - 2026-06-02

- status: `warning`
- event_count: `405891`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`378` missing=`{'sim_overbought_risk_state': 0.9894}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`359` missing=`{'simulated_order': 0.0474}` zero=`{}`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `budget_pass`: `27662`
- `orderbook_stability_observed`: `27656`
- `latency_block`: `27299`
- `swing_entry_policy_evaluated`: `25947`
- `swing_entry_micro_context_observed`: `25732`
- `strength_momentum_observed`: `20986`
- `blocked_strength_momentum`: `20986`
- `market_regime_block`: `17588`
- `bad_entry_refined_candidate`: `17453`
- `blocked_swing_score_vpw`: `17032`
- `scalp_sim_panic_scale_in_blocked`: `16309`
- `stat_action_decision_snapshot`: `13411`
- `blocked_overbought`: `10705`
- `blocked_gatekeeper_reject`: `8916`
- `market_regime_prior_observed`: `8359`
- `gatekeeper_fast_reuse_bypass`: `7961`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `7910`
- `gatekeeper_reject_cache_reuse`: `7457`
- `scalp_sim_panic_action_deduped`: `6699`
- `reversal_add_blocked_reason`: `6651`
