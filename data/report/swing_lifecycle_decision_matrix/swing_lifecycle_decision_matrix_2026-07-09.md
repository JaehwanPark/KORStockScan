# Swing Lifecycle Decision Matrix 2026-07-09

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `16040`
- probe_rows: `0`
- discovery_rows: `16040`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `274`
- complete_flow_count: `2164`
- incomplete_flow_count: `9548`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.184768`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `16040`
- bucket_count: `274`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`40` ev=`5.925292`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`34` ev=`7.435961`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`32` ev=`3.794062`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_fa5e79927f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_10d_close_equal_notional_fixed_10d` route=`sim_auto_approved` joined=`25` ev=`6.196168`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`24` ev=`13.913923`
### entry_bucket_attribution
- source_row_count: `13876`
- bucket_count: `217`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|missing_next_quote|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|gap_fade_entry|gap_fade_condition_not_met|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_limit_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|breakout_confirm_entry|breakout_not_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|missing_next_quote|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `13876`
- bucket_count: `71`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`158.980099`
- `mfe_low|mae_deep|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`8` ev=`-26.340172`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|risk_capped|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`6` ev=`-20.021528`
- `mfe_mid|mae_deep|held_missing|fixed_5d_close|risk_capped|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`3` ev=`-18.664478`
- `mfe_high|mae_low|held_missing|fixed_10d_close|risk_capped|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`10` ev=`16.827918`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `16040`
- bucket_count: `2773`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building Construction|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`39.296392`
- `next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품,중국_내수소비 확대,화장품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`37.832218`
- `next_open_entry|equal_notional|fixed_5d|Other Financial Intermediation|SI(시스템통합),전자결제,클라우드 컴퓨팅|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`23.029209`
- `bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Structural Metal Products, Tanks, Reservoirs and Steam Generators|-|RUNNER` route=`sim_auto_approved` joined=`4` ev=`22.388135`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of primary battery and secondary battery|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-19.569472`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
