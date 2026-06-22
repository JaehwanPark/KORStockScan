# Swing Lifecycle Decision Matrix 2026-06-22

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `12299`
- probe_rows: `3268`
- discovery_rows: `9031`
- raw_swing_event_count: `4939`
- ldm_consumed_event_count: `3268`
- ldm_event_coverage_rate: `0.661672`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 1413, 'swing_sim_order_bundle_assumed_filled': 66, 'swing_probe_state_restored': 51, 'swing_reentry_counterfactual_after_loss': 45, 'swing_same_symbol_loss_reentry_cooldowns_restored': 44, 'swing_probe_state_persisted': 26, 'swing_same_symbol_loss_reentry_blocked': 12, 'swing_scale_in_micro_context_observed': 8, 'swing_same_symbol_loss_reentry_cooldown': 6}`
- sim_auto_candidate_count: `25`
- workorder_count: `27`
- swing_lifecycle_flow_bucket_count: `227`
- complete_flow_count: `920`
- incomplete_flow_count: `6291`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.127583`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `12299`
- bucket_count: `227`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`16` ev=`9.025011`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`15` ev=`7.73718`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`13` ev=`2.746572`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a522265b12|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`11` ev=`9.012733`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`11` ev=`10.183507`
### entry_bucket_attribution
- source_row_count: `11348`
- bucket_count: `306`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `8206`
- bucket_count: `59`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- `mfe_high|mae_deep|held_missing|fixed_5d_close|risk_capped|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`3` ev=`18.739128`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`11` ev=`16.060691`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`14` ev=`-13.376419`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`12.389805`
- `mfe_high|mae_flat|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`10` ev=`10.259266`
### scale_in_bucket_attribution
- source_row_count: `16`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `9031`
- bucket_count: `2166`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Other Chemical Products|화장품|RUNNER` route=`sim_auto_approved` joined=`5` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Other Chemical Products|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Motor Vehicles and Engines for Motor Vehicles|그린카_하이브리드카/전기차|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Insurance|보험_손해보험|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Basic Chemicals|-|RUNNER` route=`sim_auto_approved` joined=`4` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
