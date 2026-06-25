# Swing Lifecycle Decision Matrix 2026-06-25

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `10323`
- probe_rows: `0`
- discovery_rows: `10323`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `20`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `215`
- complete_flow_count: `1024`
- incomplete_flow_count: `7251`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.123746`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `3`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `10323`
- bucket_count: `215`
- sim_auto_candidate_count: `20`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`27` ev=`6.988071`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`26` ev=`3.487886`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`20` ev=`15.275068`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`18` ev=`3.550794`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`16` ev=`10.158612`
### entry_bucket_attribution
- source_row_count: `9299`
- bucket_count: `230`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_atr_pullback_limit_entry|bottom_rebound_atr_pullback_not_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_next_open_entry|bottom_rebound_next_open|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_signal_close_retest_limit_entry|bottom_rebound_signal_close_retest_not_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BREAKOUT|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|missing_next_quote|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BREAKOUT|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|breakout_confirm_entry|missing_next_quote|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `9299`
- bucket_count: `48`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`22.052239`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`18.439521`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`23` ev=`-13.68846`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`13.507036`
- `mfe_high|mae_flat|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`17` ev=`12.681776`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `10323`
- bucket_count: `2298`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-6.59667`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Plastic Products|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-6.104238`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Electronic Components|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.717668`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품,중국_내수소비 확대,화장품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`3.035187`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Other Chemical Products|-|RUNNER` route=`sim_auto_approved` joined=`11` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
