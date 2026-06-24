# Swing Lifecycle Decision Matrix 2026-06-24

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `10293`
- probe_rows: `0`
- discovery_rows: `10293`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `226`
- complete_flow_count: `1209`
- incomplete_flow_count: `6666`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.153524`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `10293`
- bucket_count: `226`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`24` ev=`0.727018`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`23` ev=`0.507616`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`21` ev=`7.119735`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`20` ev=`3.919466`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`19` ev=`1.57148`
### entry_bucket_attribution
- source_row_count: `9084`
- bucket_count: `270`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|breakout_confirm_entry|breakout_not_touched|confidence_weighted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|next_open|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|missing_next_quote|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|breakout_confirm_entry|missing_next_quote|confidence_weighted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|nan|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_limit_touched|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `9084`
- bucket_count: `47`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`17` ev=`-13.241447`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`11` ev=`12.603381`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`11.050836`
- `mfe_high|mae_flat|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`10` ev=`10.259266`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`32` ev=`9.348364`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `10293`
- bucket_count: `2242`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Specialized Wholesale|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`8.606814`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품,중국_내수소비 확대,화장품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`4.910541`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Plastic Products|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.601903`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Other Chemical Products|-|RUNNER` route=`sim_auto_approved` joined=`13` ev=`-3.0`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Other Financial Intermediation|-|RUNNER` route=`sim_auto_approved` joined=`9` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
