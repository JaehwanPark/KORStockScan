# Observation Source Quality Audit - 2026-06-09

- status: `pass`
- event_count: `63894`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- tuning_input_allowed: `True`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- none

## Hard Blocking Row Exclusions
- none

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- none

## Reviewed Unknown Token Findings
- `scalp_entry_action_decision_snapshot` count=`2062` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`8` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=8(reviewed_missing_risk_regime_context), market_risk_state=8(reviewed_missing_risk_regime_context), liquidity_state=8(reviewed_missing_risk_regime_context), risk_regime_epoch_id=8(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`5` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`5` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`3` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`3` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`

## Top Stages
- `bad_entry_refined_candidate`: `4377`
- `scalp_sim_panic_scale_in_blocked`: `3755`
- `stat_action_decision_snapshot`: `2772`
- `budget_pass`: `2560`
- `orderbook_stability_observed`: `2560`
- `latency_block`: `2549`
- `strength_momentum_observed`: `2354`
- `blocked_strength_momentum`: `2354`
- `market_regime_prior_observed`: `2272`
- `swing_entry_policy_evaluated`: `2272`
- `swing_entry_micro_context_observed`: `2255`
- `scalp_entry_action_decision_snapshot`: `2062`
- `reversal_add_blocked_reason`: `1639`
- `blocked_gatekeeper_reject`: `1603`
- `scalp_sim_panic_action_deduped`: `1586`
- `ai_holding_fast_reuse_band`: `1581`
- `ai_holding_reuse_bypass`: `1581`
- `gatekeeper_fast_reuse_bypass`: `1553`
- `swing_probe_discarded`: `1521`
- `gatekeeper_reject_cache_reuse`: `1311`
