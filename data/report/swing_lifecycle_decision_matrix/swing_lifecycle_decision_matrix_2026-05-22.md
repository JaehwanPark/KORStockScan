# Swing Lifecycle Decision Matrix 2026-05-22

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `140399`
- probe_rows: `139109`
- discovery_rows: `1290`
- raw_swing_event_count: `143155`
- ldm_consumed_event_count: `139109`
- ldm_event_coverage_rate: `0.971737`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 3914, 'swing_reentry_counterfactual_after_loss': 59, 'swing_probe_state_persisted': 46, 'swing_scale_in_micro_context_observed': 10, 'swing_probe_state_restored': 6, 'swing_probe_state_empty_overwrite_blocked': 6, 'swing_same_symbol_loss_reentry_cooldowns_restored': 4, 'swing_same_symbol_loss_reentry_cooldown': 1}`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- swing_lifecycle_flow_bucket_count: `52`
- complete_flow_count: `51`
- incomplete_flow_count: `1171`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.041735`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `140399`
- bucket_count: `52`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_2h_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`5` ev=`2.642`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`5` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_ge_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`2` ev=`2.75`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_blocked_swing_gap_middle_discovery_ga_9ea79cd599|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_weig_04dd3ed862` route=`source_only_keep_collecting` joined=`2` ev=`8.338709`
### entry_bucket_attribution
- source_row_count: `140298`
- bucket_count: `124`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `1299`
- bucket_count: `28`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`11.822752`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`10.367749`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`9.973608`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`-3.0`
- `mfe_low|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `20`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `1290`
- bucket_count: `616`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Semiconductor|반도체_생산|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`17.087902`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`14.952596`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`6.804214`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
