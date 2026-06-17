# Swing Lifecycle Decision Matrix 2026-06-17

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `134119`
- probe_rows: `127692`
- discovery_rows: `6427`
- raw_swing_event_count: `130698`
- ldm_consumed_event_count: `127692`
- ldm_event_coverage_rate: `0.977`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 2860, 'swing_scale_in_micro_context_observed': 62, 'swing_sim_order_bundle_assumed_filled': 31, 'swing_probe_state_restored': 16, 'swing_same_symbol_loss_reentry_cooldowns_restored': 14, 'swing_probe_state_persisted': 12, 'swing_reentry_counterfactual_after_loss': 6, 'swing_same_symbol_loss_reentry_cooldown': 3, 'swing_same_symbol_loss_reentry_blocked': 2}`
- sim_auto_candidate_count: `24`
- workorder_count: `25`
- swing_lifecycle_flow_bucket_count: `142`
- complete_flow_count: `460`
- incomplete_flow_count: `5072`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.083153`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `134119`
- bucket_count: `142`
- sim_auto_candidate_count: `24`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`21` ev=`17.789738`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`12` ev=`11.004848`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`12` ev=`2.764235`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`11` ev=`12.368759`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`11` ev=`9.265582`
### entry_bucket_attribution
- source_row_count: `133639`
- bucket_count: `313`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `6013`
- bucket_count: `38`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`39` ev=`15.991328`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`14` ev=`11.698968`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`21` ev=`10.731025`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`32` ev=`10.341345`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`26` ev=`7.846613`
### scale_in_bucket_attribution
- source_row_count: `14`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `6427`
- bucket_count: `1900`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Iron and Steel|조선_해양플랜트기자재|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`11.406393`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`9.099133`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Semiconductor|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`8.70868`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Trust and collective Investment Businesses|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`4.896332`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Other Chemical Products|Cheap-Chic_저가실용품,중국_내수소비 확대,화장품|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`4.632978`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
