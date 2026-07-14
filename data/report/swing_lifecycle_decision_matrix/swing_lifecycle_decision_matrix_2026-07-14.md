# Swing Lifecycle Decision Matrix 2026-07-14

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `18942`
- probe_rows: `0`
- discovery_rows: `18942`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `287`
- complete_flow_count: `2550`
- incomplete_flow_count: `11292`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.184222`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `18942`
- bucket_count: `287`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`55` ev=`6.418233`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`45` ev=`2.178498`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_fa5e79927f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_10d_close_equal_notional_fixed_10d` route=`sim_auto_approved` joined=`38` ev=`5.898202`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`34` ev=`3.019614`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`23` ev=`10.197652`
### entry_bucket_attribution
- source_row_count: `16392`
- bucket_count: `220`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|breakout_confirm_entry|missing_next_quote|confidence_weighted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|next_open|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|missing_next_quote|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|gap_fade_entry|missing_next_quote|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|missing_next_quote|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `16392`
- bucket_count: `70`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`186.619166`
- `mfe_low|mae_deep|held_missing|trailing_after_mfe_10d_close|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`7` ev=`-36.570486`
- `mfe_high|mae_flat|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`6` ev=`24.820438`
- `mfe_low|mae_deep|held_missing|fixed_10d_close|volatility_adjusted|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`127` ev=`-19.345628`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|risk_capped|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`5` ev=`-18.574677`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `18942`
- bucket_count: `2941`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`146.874973`
- `next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Man-Made Fibers|의복_아웃도어|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-27.175508`
- `bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Structural Metal Products, Tanks, Reservoirs and Steam Generators|-|RUNNER` route=`sim_auto_approved` joined=`4` ev=`24.353314`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-21.750076`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building Construction|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`18.532921`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
