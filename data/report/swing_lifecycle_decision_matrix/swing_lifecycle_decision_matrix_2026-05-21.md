# Swing Lifecycle Decision Matrix 2026-05-21

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `255330`
- probe_rows: `254462`
- discovery_rows: `868`
- raw_swing_event_count: `262419`
- ldm_consumed_event_count: `254462`
- ldm_event_coverage_rate: `0.969678`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 7872, 'swing_probe_state_persisted': 31, 'swing_probe_state_restored': 18, 'swing_same_symbol_loss_reentry_cooldowns_restored': 16, 'swing_probe_state_empty_overwrite_blocked': 10, 'swing_scale_in_micro_context_observed': 9, 'swing_same_symbol_loss_reentry_cooldown': 1}`
- sim_auto_candidate_count: `0`
- workorder_count: `3`
- swing_lifecycle_flow_bucket_count: `41`
- complete_flow_count: `38`
- incomplete_flow_count: `791`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.045838`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `255330`
- bucket_count: `41`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_ge_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`3` ev=`2.583333`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`3` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_2h_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`2` ev=`2.605`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_blocked_swing_gap_middle_discovery_ga_9ea79cd599|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_weig_04dd3ed862` route=`source_only_keep_collecting` joined=`2` ev=`8.338709`
### entry_bucket_attribution
- source_row_count: `255260`
- bucket_count: `108`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|75_84|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|65_74|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `862`
- bucket_count: `26`
- sim_auto_candidate_count: `0`
- workorder_count: `3`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`11.822752`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`8.8999`
- `mfe_low|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`-3.0`
- `mfe_mid|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `mfe_low|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `18`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `868`
- bucket_count: `480`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`17.087902`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`14.952596`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`6.804214`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`6.603932`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`5.557783`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
