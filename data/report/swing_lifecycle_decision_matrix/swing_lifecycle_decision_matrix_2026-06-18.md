# Swing Lifecycle Decision Matrix 2026-06-18

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `22550`
- probe_rows: `15375`
- discovery_rows: `7175`
- raw_swing_event_count: `17685`
- ldm_consumed_event_count: `15375`
- ldm_event_coverage_rate: `0.869381`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 1554, 'swing_sim_order_bundle_assumed_filled': 350, 'swing_scale_in_micro_context_observed': 141, 'swing_reentry_counterfactual_after_loss': 74, 'swing_probe_state_restored': 58, 'swing_same_symbol_loss_reentry_cooldowns_restored': 57, 'swing_probe_state_persisted': 44, 'swing_same_symbol_loss_reentry_blocked': 21, 'swing_same_symbol_loss_reentry_cooldown': 11}`
- sim_auto_candidate_count: `25`
- workorder_count: `28`
- swing_lifecycle_flow_bucket_count: `186`
- complete_flow_count: `557`
- incomplete_flow_count: `5553`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.091162`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `22550`
- bucket_count: `186`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`16` ev=`14.325534`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_wei_bdea57b1fe` route=`sim_auto_approved` joined=`11` ev=`8.795684`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`9` ev=`9.697522`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`9` ev=`11.04438`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_wei_bdea57b1fe` route=`sim_auto_approved` joined=`8` ev=`8.082254`
### entry_bucket_attribution
- source_row_count: `21907`
- bucket_count: `318`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `7025`
- bucket_count: `51`
- sim_auto_candidate_count: `0`
- workorder_count: `3`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`25` ev=`15.635049`
- `mfe_high|mae_mid|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`8` ev=`12.938097`
- `mfe_high|mae_low|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`3` ev=`12.899013`
- `mfe_high|mae_deep|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`26` ev=`11.255776`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`36` ev=`10.454932`
### scale_in_bucket_attribution
- source_row_count: `61`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `7175`
- bucket_count: `2012`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of General Purpose Machinery|그린카_하이브리드카/전기차|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`21.059267`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Retail Sale in Non-Specialized Stores|백화점|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`9.190425`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`7.175425`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Instruments and Appliances for Measuring, Checking, Testing, Navigating, controlling and Other Purposes, Except Optical Instruments|원자력_설계시공|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`4.645715`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of General Purpose Machinery|원자력_기자재,화력_발전기자재|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`4.114223`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
