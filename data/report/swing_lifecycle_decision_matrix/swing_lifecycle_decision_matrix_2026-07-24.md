# Swing Lifecycle Decision Matrix 2026-07-24

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `27495`
- probe_rows: `0`
- discovery_rows: `27495`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `311`
- complete_flow_count: `3659`
- incomplete_flow_count: `16518`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.181345`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `27495`
- bucket_count: `311`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_9e715a084f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_fixed_10d_close_risk_capped_fixed_10d` route=`sim_auto_approved` joined=`79` ev=`0.891377`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`58` ev=`7.063544`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`55` ev=`6.091936`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`50` ev=`3.185659`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_fa5e79927f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_10d_close_equal_notional_fixed_10d` route=`sim_auto_approved` joined=`39` ev=`6.271444`
### entry_bucket_attribution
- source_row_count: `23836`
- bucket_count: `192`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_signal_close_retest_limit_entry|bottom_rebound_signal_close_retest_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_atr_pullback_limit_entry|bottom_rebound_atr_pullback_not_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|missing_next_quote|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|next_open|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_not_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `23836`
- bucket_count: `85`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`168.698373`
- `mfe_high|mae_low|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`16` ev=`57.009165`
- `mfe_high|mae_low|held_missing|fixed_10d_close|risk_capped|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`18` ev=`39.942146`
- `mfe_high|mae_mid|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`44` ev=`20.71976`
- `mfe_low|mae_deep|held_missing|fixed_10d_close|volatility_adjusted|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`230` ev=`-19.58632`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `27495`
- bucket_count: `2796`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Precious Metals and Ornamentations|-|RUNNER` route=`sim_auto_approved` joined=`3` ev=`-43.922406`
- `bottom_rebound_signal_close_retest_limit_entry|risk_capped|fixed_10d|Manufacture of Precious Metals and Ornamentations|-|RUNNER` route=`sim_auto_approved` joined=`3` ev=`-43.54229`
- `bottom_rebound_signal_close_retest_limit_entry|risk_capped|fixed_10d|Sea and Coastal Water Transport|-|RUNNER` route=`sim_auto_approved` joined=`3` ev=`31.697555`
- `next_open_entry|volatility_adjusted|fixed_10d|Other Specialized Wholesale|자원개발 E&P|DIAGNOSTIC` route=`sim_auto_approved` joined=`7` ev=`-25.57632`
- `next_open_entry|volatility_adjusted|fixed_10d|Trust and collective Investment Businesses|창투|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`25.304897`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
