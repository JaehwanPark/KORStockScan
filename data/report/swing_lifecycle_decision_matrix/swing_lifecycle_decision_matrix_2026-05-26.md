# Swing Lifecycle Decision Matrix 2026-05-26

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `203216`
- probe_rows: `201344`
- discovery_rows: `1872`
- raw_swing_event_count: `210156`
- ldm_consumed_event_count: `201344`
- ldm_event_coverage_rate: `0.958069`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 8029, 'swing_reentry_counterfactual_after_loss': 528, 'swing_probe_state_persisted': 98, 'swing_probe_state_restored': 57, 'swing_same_symbol_loss_reentry_cooldowns_restored': 48, 'swing_scale_in_micro_context_observed': 19, 'swing_sim_scale_in_order_assumed_filled': 19, 'swing_same_symbol_loss_reentry_cooldown': 10, 'swing_probe_state_empty_overwrite_blocked': 4}`
- sim_auto_candidate_count: `0`
- workorder_count: `8`
- swing_lifecycle_flow_bucket_count: `69`
- complete_flow_count: `20`
- incomplete_flow_count: `1905`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.01039`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_DROUGHT_CRITICAL`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `203216`
- bucket_count: `69`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`12` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`12` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`11` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`11` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`11` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `203065`
- bucket_count: `149`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BOTTOM|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `1944`
- bucket_count: `53`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`3` ev=`14.0256`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`12.677995`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`8` ev=`11.037027`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`12` ev=`-3.0`
- `mfe_low|mae_deep|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`12` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `19`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `1872`
- bucket_count: `840`
- sim_auto_candidate_count: `0`
- workorder_count: `3`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`10.317317`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`7.133939`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`6.15246`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
