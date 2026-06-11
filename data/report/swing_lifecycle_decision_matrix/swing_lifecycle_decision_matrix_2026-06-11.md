# Swing Lifecycle Decision Matrix 2026-06-11

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `36301`
- probe_rows: `32587`
- discovery_rows: `3714`
- raw_swing_event_count: `39609`
- ldm_consumed_event_count: `32587`
- ldm_event_coverage_rate: `0.822717`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 5449, 'market_regime_block': 1225, 'swing_probe_state_persisted': 78, 'swing_probe_state_restored': 66, 'swing_same_symbol_loss_reentry_cooldowns_restored': 58, 'swing_sim_order_bundle_assumed_filled': 57, 'swing_scale_in_micro_context_observed': 36, 'swing_reentry_counterfactual_after_loss': 32, 'swing_same_symbol_loss_reentry_cooldown': 9, 'swing_same_symbol_loss_reentry_blocked': 8, 'swing_probe_state_empty_overwrite_blocked': 4}`
- sim_auto_candidate_count: `1`
- workorder_count: `21`
- swing_lifecycle_flow_bucket_count: `133`
- complete_flow_count: `294`
- incomplete_flow_count: `2889`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.092366`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `3`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `36301`
- bucket_count: `133`
- sim_auto_candidate_count: `1`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weigh_f216b9c539` route=`sim_auto_approved` joined=`4` ev=`3.173906`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_aa5acd00c4|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_volatility_adjusted_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_volatility_adjusted_mae_2e05582a7d` route=`source_only_keep_collecting` joined=`27` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3692b81ae8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`12` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_895f9502b5|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`12` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_s_b59dd3d98c` route=`source_only_keep_collecting` joined=`11` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `35935`
- bucket_count: `287`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `3554`
- bucket_count: `49`
- sim_auto_candidate_count: `0`
- workorder_count: `8`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`14.764236`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`13.915303`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`13.89037`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`8.387507`
- `mfe_mid|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`3.702004`
### scale_in_bucket_attribution
- source_row_count: `34`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `3714`
- bucket_count: `1461`
- sim_auto_candidate_count: `0`
- workorder_count: `13`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Banking and Savings Institutions|은행|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`18.954726`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`7.31432`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Iron and Steel|조선_해양플랜트기자재|DIAGNOSTIC` route=`code_patch_required` joined=`3` ev=`5.706237`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`5.318808`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
