# Swing Lifecycle Decision Matrix 2026-05-20

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `369400`
- probe_rows: `368974`
- discovery_rows: `426`
- raw_swing_event_count: `378461`
- ldm_consumed_event_count: `368974`
- ldm_event_coverage_rate: `0.974933`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 9216, 'swing_reentry_counterfactual_after_loss': 204, 'swing_probe_state_persisted': 27, 'swing_probe_state_restored': 11, 'swing_scale_in_micro_context_observed': 9, 'swing_same_symbol_loss_reentry_cooldowns_restored': 9, 'swing_same_symbol_loss_reentry_cooldown': 8, 'swing_probe_state_empty_overwrite_blocked': 3}`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- swing_lifecycle_flow_bucket_count: `28`
- complete_flow_count: `16`
- incomplete_flow_count: `415`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.037123`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `369400`
- bucket_count: `28`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-3.025`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_ge_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-3.555`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-3.11`
- `entry=swing_entry:entry_bucket_attribution:blocked_gatekeeper_reject_kospi_base_flat_up_lt55_vpw_extreme_kospi_m_f0dd798d01|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-3.11`
### entry_bucket_attribution
- source_row_count: `369351`
- bucket_count: `102`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BOTTOM|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `440`
- bucket_count: `26`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`7.624574`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`5.296621`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`source_only_keep_collecting` joined=`1` ev=`2.851432`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`-2.0`
- `mfe_low|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`-2.0`
### scale_in_bucket_attribution
- source_row_count: `18`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `426`
- bucket_count: `344`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`8.647386`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`3.812287`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`3.216356`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.851432`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.06646`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
