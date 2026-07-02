# Swing Lifecycle Decision Matrix 2026-07-02

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `12565`
- probe_rows: `0`
- discovery_rows: `12565`
- raw_swing_event_count: `0`
- ldm_consumed_event_count: `0`
- ldm_event_coverage_rate: `0.0`
- unmapped_swing_stage_counts: `{}`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `241`
- complete_flow_count: `1361`
- incomplete_flow_count: `8482`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.138271`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `12565`
- bucket_count: `241`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`28` ev=`0.019315`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`24` ev=`3.969869`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`21` ev=`7.119735`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`20` ev=`1.357364`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_trailing_after_mfe_stop_confidence_weig_cadb5f3b06` route=`sim_auto_approved` joined=`16` ev=`3.34778`
### entry_bucket_attribution
- source_row_count: `11204`
- bucket_count: `230`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_next_open_entry|bottom_rebound_next_open|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_signal_close_retest_limit_entry|bottom_rebound_signal_close_retest_not_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_signal_close_retest_limit_entry|bottom_rebound_signal_close_retest_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|missing_next_quote|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|bottom_rebound_atr_pullback_limit_entry|bottom_rebound_atr_pullback_not_touched|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `11204`
- bucket_count: `60`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`18` ev=`73.170505`
- `mfe_low|mae_deep|held_missing|fixed_10d_close|volatility_adjusted|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`6` ev=`-21.702741`
- `mfe_mid|mae_deep|held_missing|fixed_10d_close|volatility_adjusted|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`14` ev=`-20.591002`
- `mfe_mid|mae_deep|held_missing|fixed_5d_close|risk_capped|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`11` ev=`-17.725131`
- `mfe_high|mae_mid|held_missing|fixed_10d_close|volatility_adjusted|fixed_10d|-|-|-` route=`sim_auto_approved` joined=`3` ev=`15.459428`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `12565`
- bucket_count: `2482`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Man-Made Fibers|의복_아웃도어|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-17.521064`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of primary battery and secondary battery|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-16.244098`
- `next_open_entry|equal_notional|fixed_5d|Other Financial Intermediation|SI(시스템통합),전자결제,클라우드 컴퓨팅|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`15.939921`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|자동차_전장화 수혜|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-13.253723`
- `next_open_entry|equal_notional|fixed_5d|Manufacture of Motor Vehicles and Engines for Motor Vehicles|그린카_하이브리드카/전기차|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-13.208422`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
