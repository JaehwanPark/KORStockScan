# Swing Lifecycle Decision Matrix 2026-06-15

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `68551`
- probe_rows: `63487`
- discovery_rows: `5064`
- raw_swing_event_count: `65816`
- ldm_consumed_event_count: `63487`
- ldm_event_coverage_rate: `0.964613`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 1619, 'swing_scale_in_micro_context_observed': 595, 'swing_sim_order_bundle_assumed_filled': 69, 'swing_probe_state_restored': 27, 'swing_probe_state_persisted': 14, 'swing_same_symbol_loss_reentry_cooldowns_restored': 3, 'swing_probe_state_empty_overwrite_blocked': 2}`
- sim_auto_candidate_count: `18`
- workorder_count: `26`
- swing_lifecycle_flow_bucket_count: `150`
- complete_flow_count: `380`
- incomplete_flow_count: `3950`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.08776`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `68551`
- bucket_count: `150`
- sim_auto_candidate_count: `18`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`13` ev=`2.987131`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_wei_bdea57b1fe` route=`sim_auto_approved` joined=`9` ev=`6.887256`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`9` ev=`2.689462`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_flat_held_missing_trailing_after_mfe_stop_confidence_weig_9a307dc95f` route=`sim_auto_approved` joined=`8` ev=`3.16665`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_wei_bdea57b1fe` route=`sim_auto_approved` joined=`7` ev=`7.931443`
### entry_bucket_attribution
- source_row_count: `68144`
- bucket_count: `287`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `4771`
- bucket_count: `39`
- sim_auto_candidate_count: `0`
- workorder_count: `1`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`10` ev=`24.164759`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`17` ev=`12.435844`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`15` ev=`12.004873`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`7` ev=`10.495417`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`27` ev=`8.091553`
### scale_in_bucket_attribution
- source_row_count: `19`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `5064`
- bucket_count: `1715`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building Construction|건설_국내주택,건설_해외건설|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`9.373167`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`5.179751`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`3.05427`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Insurance|보험_손해보험|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
