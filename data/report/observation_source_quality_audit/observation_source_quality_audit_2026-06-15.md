# Observation Source Quality Audit - 2026-06-15

- status: `pass`
- event_count: `261163`
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
- `latency_block` count=`16408` routing=`reviewed_unknown_token_provenance` fields=`ws_age_ms=2(reviewed_pre_contract_placeholder), ws_jitter_ms=2(reviewed_pre_contract_placeholder)`
- `scalp_entry_action_decision_snapshot` count=`4676` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context), sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_buy_order_assumed_filled` count=`275` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_buy_order_virtual_pending` count=`275` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_entry_armed` count=`275` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_holding_started` count=`275` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`275` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `lifecycle_decision_matrix_runtime_policy` count=`106` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`80` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`69` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`69` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`47` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=47(reviewed_missing_risk_regime_context), market_risk_state=47(reviewed_missing_risk_regime_context), liquidity_state=47(reviewed_missing_risk_regime_context), risk_regime_epoch_id=47(reviewed_missing_risk_regime_context)`
- `position_rebased_after_fill` count=`16` routing=`reviewed_unknown_token_provenance` fields=`fill_quality=4(reviewed_fill_quality_pre_contract_no_requested_qty)`
- `preset_exit_sync_ok` count=`12` routing=`reviewed_unknown_token_provenance` fields=`fill_quality=2(reviewed_fill_quality_pre_contract_no_requested_qty)`
- `order_bundle_submitted` count=`11` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=11(reviewed_pre_contract_placeholder), remaining_qty=11(reviewed_pre_contract_placeholder), fill_quality=11(reviewed_pre_contract_placeholder)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`2` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available), __stage=2(reviewed_explicit_sim_liquidity_unknown_stage)`

## Top Stages
- `budget_pass`: `16568`
- `orderbook_stability_observed`: `16566`
- `latency_block`: `16408`
- `market_regime_prior_observed`: `16009`
- `swing_entry_policy_evaluated`: `16009`
- `swing_entry_micro_context_observed`: `16009`
- `bad_entry_refined_candidate`: `13653`
- `scalp_sim_panic_scale_in_blocked`: `12096`
- `blocked_gatekeeper_reject`: `9920`
- `blocked_swing_gap`: `9200`
- `gatekeeper_fast_reuse_bypass`: `9083`
- `strength_momentum_observed`: `8955`
- `blocked_strength_momentum`: `8955`
- `stat_action_decision_snapshot`: `7849`
- `gatekeeper_reject_cache_reuse`: `7633`
- `reversal_add_blocked_reason`: `6770`
- `blocked_swing_score_vpw`: `6084`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `5075`
- `scalp_sim_panic_action_deduped`: `4928`
- `scalp_entry_action_decision_snapshot`: `4676`
