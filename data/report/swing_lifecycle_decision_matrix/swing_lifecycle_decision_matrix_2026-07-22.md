# Swing Lifecycle Decision Matrix 2026-07-22

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `25115`
- probe_rows: `0`
- discovery_rows: `25115`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `305`
- complete_flow_count: `3424`
- incomplete_flow_count: `14843`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.187442`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `25115`
- bucket_count: `305`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_9e715a084f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_fixed_10d_close_risk_capped_fixed_10d` route=`sim_auto_approved` joined=`87` ev=`1.031046`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`57` ev=`7.034474`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`52` ev=`6.104927`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_fa5e79927f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_10d_close_equal_notional_fixed_10d` route=`sim_auto_approved` joined=`39` ev=`6.271444`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_9e715a084f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_10d_close_risk_capped_fixed_10d` route=`sim_auto_approved` joined=`34` ev=`7.580583`
### entry_bucket_attribution
- source_row_count: `21691`
- bucket_count: `194`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|MIDDLE|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|next_open|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_signal_close_retest_limit_entry|bottom_rebound_signal_close_retest_not_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_atr_pullback_limit_entry|bottom_rebound_atr_pullback_not_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|gap_fade_entry|gap_fade_condition_not_met|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_not_touched|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `21691`
- bucket_count: `81`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_low|held_missing|fixed_10d_close|risk_capped|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`13` ev=`39.662262`
- `mfe_low|mae_deep|held_missing|trailing_after_mfe_10d_close|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`-37.99448`
- `mfe_high|mae_mid|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`44` ev=`29.453761`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`25.379922`
- `mfe_high|mae_deep|held_missing|scale_in_recovery_10d_close|volatility_adjusted|scale_in_recovery|-|-|-` route=`sim_auto_approved` joined=`7` ev=`-23.814287`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `25115`
- bucket_count: `2709`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Precious Metals and Ornamentations|-|RUNNER` route=`sim_auto_approved` joined=`3` ev=`-43.922406`
- `bottom_rebound_signal_close_retest_limit_entry|risk_capped|fixed_10d|Manufacture of Precious Metals and Ornamentations|-|RUNNER` route=`sim_auto_approved` joined=`3` ev=`-43.767896`
- `bottom_rebound_signal_close_retest_limit_entry|risk_capped|fixed_10d|Sea and Coastal Water Transport|-|RUNNER` route=`sim_auto_approved` joined=`3` ev=`31.171292`
- `next_open_entry|volatility_adjusted|fixed_10d|Other Specialized Wholesale|자원개발 E&P|DIAGNOSTIC` route=`sim_auto_approved` joined=`7` ev=`-25.57632`
- `next_open_entry|volatility_adjusted|fixed_10d|Trust and collective Investment Businesses|창투|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`25.304897`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
