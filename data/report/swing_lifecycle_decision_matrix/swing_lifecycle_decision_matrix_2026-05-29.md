# Swing Lifecycle Decision Matrix 2026-05-29

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `63935`
- probe_rows: `59873`
- discovery_rows: `4062`
- raw_swing_event_count: `63539`
- ldm_consumed_event_count: `59873`
- ldm_event_coverage_rate: `0.942303`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 3350, 'swing_probe_state_restored': 67, 'swing_probe_state_persisted': 60, 'swing_same_symbol_loss_reentry_cooldowns_restored': 58, 'swing_sim_order_bundle_assumed_filled': 44, 'swing_reentry_counterfactual_after_loss': 44, 'swing_scale_in_micro_context_observed': 25, 'swing_same_symbol_loss_reentry_blocked': 12, 'swing_same_symbol_loss_reentry_cooldown': 6}`
- sim_auto_candidate_count: `1`
- workorder_count: `9`
- swing_lifecycle_flow_bucket_count: `59`
- complete_flow_count: `65`
- incomplete_flow_count: `3907`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.016365`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `63935`
- bucket_count: `59`
- sim_auto_candidate_count: `1`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_weig_04dd3ed862` route=`sim_auto_approved` joined=`3` ev=`13.044439`
- `entry=swing_entry:entry_bucket_attribution:missing_missing_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:missing_missing_held_missing_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`3` ev=`-2.536667`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`3` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_895f9502b5|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `63809`
- bucket_count: `248`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|BOTTOM|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `4109`
- bucket_count: `38`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`16.469822`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`12.206175`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`9.728392`
- `mfe_mid|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`3.273902`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`9` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `36`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `4062`
- bucket_count: `1406`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`11.426158`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`5.89765`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`5.866828`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`code_patch_required` joined=`4` ev=`5.695071`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Software Development and Supply|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`5.346042`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
