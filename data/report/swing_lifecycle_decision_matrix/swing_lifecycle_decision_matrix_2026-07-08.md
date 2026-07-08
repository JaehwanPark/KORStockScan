# Swing Lifecycle Decision Matrix 2026-07-08

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `15298`
- probe_rows: `0`
- discovery_rows: `15298`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `275`
- complete_flow_count: `1921`
- incomplete_flow_count: `9535`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.167685`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `15298`
- bucket_count: `275`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`39` ev=`2.099041`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_fa5e79927f|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_10d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_10d_close_equal_notional_fixed_10d` route=`sim_auto_approved` joined=`34` ev=`6.324277`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`25` ev=`4.224867`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`23` ev=`7.527427`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`21` ev=`1.553893`
### entry_bucket_attribution
- source_row_count: `13377`
- bucket_count: `229`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|gap_fade_entry|gap_fade_condition_not_met|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_limit_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|breakout_confirm_entry|breakout_not_touched|confidence_weighted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_limit_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_not_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `13377`
- bucket_count: `70`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`13` ev=`86.860324`
- `mfe_low|mae_deep|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`8` ev=`-26.824704`
- `mfe_high|mae_flat|held_missing|fixed_10d_close|equal_notional|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`6` ev=`24.820438`
- `mfe_low|mae_deep|held_missing|fixed_10d_close|volatility_adjusted|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`16` ev=`-23.930136`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|risk_capped|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`4` ev=`-17.013764`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `15298`
- bucket_count: `2754`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `next_open_entry|volatility_adjusted|fixed_10d|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품,중국_내수소비 확대,화장품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`44.363624`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Building Construction|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`23.497402`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-21.750076`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Semiconductor|반도체_생산,반도체_시스템반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-17.799692`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Special-Purpose Machinery|반도체_후공정장비|DIAGNOSTIC` route=`sim_auto_approved` joined=`7` ev=`-17.710437`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
