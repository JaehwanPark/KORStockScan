# Observation Source Quality Audit - 2026-05-27

- status: `fail`
- event_count: `453117`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`389` missing=`{'sim_overbought_risk_state': 0.9769}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`167` missing=`{'simulated_order': 0.006}` zero=`{}`
- `swing_same_symbol_loss_reentry_cooldown` sample=`6` missing=`{'source_probe_id': 0.3333}` zero=`{}`

## Invalid Label Findings
- `swing_reentry_counterfactual_after_loss` field=`gatekeeper_action` count=`9` routing=`source_quality_blocker` examples=`['NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR']`
- `swing_probe_entry_candidate` field=`gatekeeper_action` count=`46` routing=`source_quality_blocker` examples=`['NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR']`
- `swing_probe_holding_started` field=`gatekeeper_action` count=`46` routing=`source_quality_blocker` examples=`['NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR', 'NOT_EVALUATED_SCORE_VPW_PRIOR']`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `budget_pass`: `37059`
- `orderbook_stability_observed`: `37032`
- `latency_block`: `36812`
- `swing_entry_policy_evaluated`: `34885`
- `swing_entry_micro_context_observed`: `34630`
- `blocked_swing_score_vpw`: `33794`
- `market_regime_prior_observed`: `25224`
- `strength_momentum_observed`: `18339`
- `blocked_strength_momentum`: `18339`
- `bad_entry_refined_candidate`: `16996`
- `scalp_sim_panic_scale_in_blocked`: `16329`
- `stat_action_decision_snapshot`: `12597`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `10496`
- `market_regime_block`: `9661`
- `blocked_overbought`: `8813`
- `swing_probe_discarded`: `7715`
- `reversal_add_blocked_reason`: `6978`
- `scalp_sim_panic_action_deduped`: `6683`
- `scalp_entry_action_decision_snapshot`: `6660`
- `ai_holding_fast_reuse_band`: `6018`
