# Swing Lifecycle Decision Matrix 2026-06-16

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `76318`
- probe_rows: `70531`
- discovery_rows: `5787`
- raw_swing_event_count: `75472`
- ldm_consumed_event_count: `70531`
- ldm_event_coverage_rate: `0.934532`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 4064, 'swing_scale_in_micro_context_observed': 703, 'swing_sim_order_bundle_assumed_filled': 79, 'swing_probe_state_restored': 30, 'swing_same_symbol_loss_reentry_cooldowns_restored': 21, 'swing_probe_state_persisted': 18, 'swing_reentry_counterfactual_after_loss': 17, 'swing_same_symbol_loss_reentry_blocked': 6, 'swing_same_symbol_loss_reentry_cooldown': 3}`
- sim_auto_candidate_count: `24`
- workorder_count: `27`
- swing_lifecycle_flow_bucket_count: `169`
- complete_flow_count: `433`
- incomplete_flow_count: `4520`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.087422`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `76318`
- bucket_count: `169`
- sim_auto_candidate_count: `24`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`17` ev=`14.205358`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`11` ev=`12.85031`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`9` ev=`14.291363`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`8` ev=`2.742745`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_wei_bdea57b1fe` route=`sim_auto_approved` joined=`7` ev=`6.916828`
### entry_bucket_attribution
- source_row_count: `75861`
- bucket_count: `306`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|65_74|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `5457`
- bucket_count: `39`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`47` ev=`14.04345`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`23` ev=`12.343956`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`12` ev=`10.468041`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`13` ev=`10.076041`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`23` ev=`9.070979`
### scale_in_bucket_attribution
- source_row_count: `13`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `5787`
- bucket_count: `1802`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of General Purpose Machinery|그린카_하이브리드카/전기차|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`24.105846`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`7.808165`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Activities Auxiliary to Financial Service Activities|증권|MAIN` route=`sim_auto_approved` joined=`4` ev=`4.758041`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|PCB(인쇄회로기판)|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
