# Observation Source Quality Audit - 2026-06-12

- status: `pass`
- event_count: `194253`
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
- `latency_block` count=`12209` routing=`reviewed_unknown_token_provenance` fields=`ws_age_ms=30(reviewed_pre_contract_placeholder), ws_jitter_ms=30(reviewed_pre_contract_placeholder)`
- `scalp_entry_action_decision_snapshot` count=`7191` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available), risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_buy_order_assumed_filled` count=`724` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available)`
- `scalp_sim_buy_order_virtual_pending` count=`724` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available)`
- `scalp_sim_entry_armed` count=`724` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available)`
- `scalp_sim_holding_started` count=`724` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`711` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available)`
- `scalp_sim_panic_context_warning` count=`246` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=246(reviewed_missing_risk_regime_context), market_risk_state=246(reviewed_missing_risk_regime_context), liquidity_state=246(reviewed_missing_risk_regime_context), risk_regime_epoch_id=246(reviewed_missing_risk_regime_context)`
- `position_rebased_after_fill` count=`242` routing=`reviewed_unknown_token_provenance` fields=`fill_quality=60(reviewed_fill_quality_pre_contract_no_requested_qty)`
- `preset_exit_sync_ok` count=`180` routing=`reviewed_unknown_token_provenance` fields=`fill_quality=30(reviewed_fill_quality_pre_contract_no_requested_qty)`
- `lifecycle_decision_matrix_runtime_policy` count=`126` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`124` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`74` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`74` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`37` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=37(reviewed_pre_contract_placeholder), remaining_qty=37(reviewed_pre_contract_placeholder), fill_quality=37(reviewed_pre_contract_placeholder)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`30` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=30(reviewed_sim_liquidity_not_available), __stage=30(reviewed_explicit_sim_liquidity_unknown_stage)`

## Top Stages
- `budget_pass`: `12398`
- `orderbook_stability_observed`: `12364`
- `latency_block`: `12209`
- `market_regime_prior_observed`: `10392`
- `swing_entry_policy_evaluated`: `10392`
- `swing_entry_micro_context_observed`: `10388`
- `bad_entry_refined_candidate`: `10118`
- `strength_momentum_observed`: `8280`
- `blocked_strength_momentum`: `8280`
- `stat_action_decision_snapshot`: `7978`
- `scalp_entry_action_decision_snapshot`: `7191`
- `reversal_add_blocked_reason`: `6210`
- `blocked_swing_score_vpw`: `5198`
- `blocked_gatekeeper_reject`: `5193`
- `gatekeeper_fast_reuse_bypass`: `5133`
- `swing_probe_discarded`: `4645`
- `ai_holding_fast_reuse_band`: `3573`
- `ai_holding_reuse_bypass`: `3573`
- `gatekeeper_reject_cache_reuse`: `3181`
- `blocked_swing_gap`: `2761`
