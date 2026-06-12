# Swing Lifecycle Decision Matrix 2026-06-12

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `43764`
- probe_rows: `39352`
- discovery_rows: `4412`
- raw_swing_event_count: `44538`
- ldm_consumed_event_count: `39352`
- ldm_event_coverage_rate: `0.88356`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 4645, 'swing_scale_in_micro_context_observed': 330, 'swing_sim_order_bundle_assumed_filled': 74, 'swing_probe_state_restored': 32, 'swing_probe_state_persisted': 29, 'swing_probe_state_empty_overwrite_blocked': 27, 'swing_same_symbol_loss_reentry_cooldowns_restored': 23, 'swing_reentry_counterfactual_after_loss': 16, 'swing_same_symbol_loss_reentry_cooldown': 6, 'swing_same_symbol_loss_reentry_blocked': 4}`
- sim_auto_candidate_count: `4`
- workorder_count: `29`
- swing_lifecycle_flow_bucket_count: `157`
- complete_flow_count: `360`
- incomplete_flow_count: `3375`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.096386`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `43764`
- bucket_count: `157`
- sim_auto_candidate_count: `4`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_trailing_after_mfe_stop_confidence_weig_cadb5f3b06` route=`sim_auto_approved` joined=`5` ev=`3.616884`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_wei_b4cd7a0613` route=`sim_auto_approved` joined=`4` ev=`13.281604`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`3` ev=`15.378545`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`3` ev=`3.67981`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_aa5acd00c4|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_volatility_adjusted_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched_volatility_adjusted_mae_628395d58a` route=`source_only_keep_collecting` joined=`17` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `43354`
- bucket_count: `269`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|KOSPI_BASE|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BOTTOM|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `4162`
- bucket_count: `41`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`22.427994`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`15.034934`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`9` ev=`14.411569`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`9` ev=`13.360383`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`13.301261`
### scale_in_bucket_attribution
- source_row_count: `33`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `4412`
- bucket_count: `1593`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Telecommunication and Broadcasting Apparatuses|반도체_생산|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Amusement and theme Park Operation|카지노|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Building Construction|건설_국내주택,건설_해외건설|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
