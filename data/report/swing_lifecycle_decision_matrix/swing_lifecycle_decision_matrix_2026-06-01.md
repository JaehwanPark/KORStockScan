# Swing Lifecycle Decision Matrix 2026-06-01

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `95919`
- probe_rows: `91483`
- discovery_rows: `4436`
- raw_swing_event_count: `96819`
- ldm_consumed_event_count: `91483`
- ldm_event_coverage_rate: `0.944887`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 5132, 'swing_probe_state_persisted': 58, 'swing_probe_state_restored': 51, 'swing_same_symbol_loss_reentry_cooldowns_restored': 41, 'swing_reentry_counterfactual_after_loss': 25, 'swing_scale_in_micro_context_observed': 15, 'swing_same_symbol_loss_reentry_cooldown': 5, 'swing_sim_order_bundle_assumed_filled': 5, 'swing_same_symbol_loss_reentry_blocked': 4}`
- sim_auto_candidate_count: `0`
- workorder_count: `8`
- swing_lifecycle_flow_bucket_count: `46`
- complete_flow_count: `47`
- incomplete_flow_count: `4314`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.010777`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `95919`
- bucket_count: `46`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_lt_30m_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`2` ev=`2.625`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_wei_b4cd7a0613` route=`source_only_keep_collecting` joined=`2` ev=`8.319184`
### entry_bucket_attribution
- source_row_count: `95812`
- bucket_count: `251`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_gatekeeper_reject|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `4461`
- bucket_count: `30`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`13.197418`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`9.575071`
- `mfe_mid|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`4.272599`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`-3.0`
- `mfe_mid|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `30`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `4436`
- bucket_count: `1406`
- sim_auto_candidate_count: `0`
- workorder_count: `3`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`10.764688`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`5.317882`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`5.287515`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`code_patch_required` joined=`4` ev=`4.871991`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Software Development and Supply|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`4.774426`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
