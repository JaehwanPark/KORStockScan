# Observation Source Quality Audit - 2026-06-12

- status: `warning`
- event_count: `104973`
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
- `scalp_entry_action_decision_snapshot` count=`4546` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(0.0048)`
- `scalp_sim_buy_order_assumed_filled` count=`501` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(0.0439)`
- `scalp_sim_buy_order_virtual_pending` count=`501` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(0.0439)`
- `scalp_sim_entry_armed` count=`501` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(0.0439)`
- `scalp_sim_holding_started` count=`501` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(0.0439)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`493` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(0.0446)`
- `position_rebased_after_fill` count=`177` routing=`source_quality_blocker_or_provenance_backfill` fields=`fill_quality=44(0.2486)`
- `preset_exit_sync_ok` count=`132` routing=`source_quality_blocker_or_provenance_backfill` fields=`fill_quality=22(0.1667)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`22` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=22(1.0), __stage=22(1.0)`

## Reviewed Unknown Token Findings
- `latency_block` count=`7403` routing=`reviewed_unknown_token_provenance` fields=`ws_age_ms=22(reviewed_pre_contract_placeholder), ws_jitter_ms=22(reviewed_pre_contract_placeholder)`
- `scalp_entry_action_decision_snapshot` count=`4546` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`95` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=95(reviewed_missing_risk_regime_context), market_risk_state=95(reviewed_missing_risk_regime_context), liquidity_state=95(reviewed_missing_risk_regime_context), risk_regime_epoch_id=95(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`52` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=7(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`51` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=7(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`23` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=23(reviewed_pre_contract_placeholder), remaining_qty=23(reviewed_pre_contract_placeholder), fill_quality=23(reviewed_pre_contract_placeholder)`

## Top Stages
- `budget_pass`: `7504`
- `orderbook_stability_observed`: `7481`
- `latency_block`: `7403`
- `market_regime_prior_observed`: `6045`
- `swing_entry_policy_evaluated`: `6045`
- `swing_entry_micro_context_observed`: `6044`
- `strength_momentum_observed`: `5103`
- `blocked_strength_momentum`: `5103`
- `scalp_entry_action_decision_snapshot`: `4546`
- `bad_entry_refined_candidate`: `4418`
- `blocked_swing_score_vpw`: `3948`
- `stat_action_decision_snapshot`: `3508`
- `reversal_add_blocked_reason`: `2686`
- `swing_probe_discarded`: `2104`
- `blocked_gatekeeper_reject`: `2097`
- `gatekeeper_fast_reuse_bypass`: `2092`
- `blocked_swing_gap`: `1596`
- `gatekeeper_reject_cache_reuse`: `1351`
- `ai_holding_fast_reuse_band`: `1148`
- `ai_holding_reuse_bypass`: `1148`
