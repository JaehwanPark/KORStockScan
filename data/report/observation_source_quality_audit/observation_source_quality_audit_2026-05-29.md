# Observation Source Quality Audit - 2026-05-29

- status: `warning`
- event_count: `273235`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `blocked_overbought` sample=`11867` missing=`{}` zero=`{'intraday_range_pct': 0.1458}`
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`192` missing=`{'sim_overbought_risk_state': 0.9375}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`192` missing=`{'simulated_order': 0.0781}` zero=`{}`
- `swing_same_symbol_loss_reentry_cooldown` sample=`6` missing=`{'source_probe_id': 0.6667}` zero=`{}`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `strength_momentum_observed`: `25534`
- `blocked_strength_momentum`: `25534`
- `budget_pass`: `16148`
- `orderbook_stability_observed`: `16136`
- `latency_block`: `16003`
- `market_regime_prior_observed`: `14822`
- `swing_entry_policy_evaluated`: `14822`
- `swing_entry_micro_context_observed`: `14638`
- `blocked_swing_score_vpw`: `11877`
- `blocked_overbought`: `11867`
- `scalp_sim_panic_scale_in_blocked`: `10263`
- `bad_entry_refined_candidate`: `9774`
- `stat_action_decision_snapshot`: `8126`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `7536`
- `scalp_sim_panic_action_deduped`: `4160`
- `scalp_entry_action_decision_snapshot`: `4106`
- `ai_holding_fast_reuse_band`: `4016`
- `ai_holding_reuse_bypass`: `4000`
- `blocked_swing_gap`: `3512`
- `holding_flow_override_defer_exit`: `3429`
