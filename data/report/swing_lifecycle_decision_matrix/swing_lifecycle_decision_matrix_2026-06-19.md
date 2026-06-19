# Swing Lifecycle Decision Matrix 2026-06-19

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `11809`
- probe_rows: `4079`
- discovery_rows: `7730`
- raw_swing_event_count: `5814`
- ldm_consumed_event_count: `4079`
- ldm_event_coverage_rate: `0.701582`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 1194, 'swing_sim_order_bundle_assumed_filled': 133, 'market_regime_block': 104, 'swing_reentry_counterfactual_after_loss': 84, 'swing_probe_state_restored': 57, 'swing_same_symbol_loss_reentry_cooldowns_restored': 55, 'swing_probe_state_persisted': 40, 'swing_same_symbol_loss_reentry_blocked': 28, 'swing_scale_in_micro_context_observed': 27, 'swing_same_symbol_loss_reentry_cooldown': 13}`
- sim_auto_candidate_count: `25`
- workorder_count: `29`
- swing_lifecycle_flow_bucket_count: `182`
- complete_flow_count: `540`
- incomplete_flow_count: `6146`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.080766`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `3`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `11809`
- bucket_count: `182`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`13` ev=`10.101289`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`12` ev=`22.764282`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_wei_b4cd7a0613` route=`sim_auto_approved` joined=`11` ev=`10.234392`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`10` ev=`8.189417`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`9` ev=`7.364078`
### entry_bucket_attribution
- source_row_count: `11212`
- bucket_count: `325`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `7370`
- bucket_count: `51`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`20` ev=`19.903421`
- `mfe_high|mae_flat|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`13` ev=`15.214413`
- `mfe_high|mae_low|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`50` ev=`14.356693`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`23` ev=`11.800946`
- `mfe_high|mae_mid|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`26` ev=`10.005178`
### scale_in_bucket_attribution
- source_row_count: `34`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `7730`
- bucket_count: `2125`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`20.712918`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Retail Sale in Non-Specialized Stores|백화점|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`11.339917`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Iron and Steel|조선_해양플랜트기자재|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`7.698839`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Instruments and Appliances for Measuring, Checking, Testing, Navigating, controlling and Other Purposes, Except Optical Instruments|원자력_설계시공|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`4.600926`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|증권,창투|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
