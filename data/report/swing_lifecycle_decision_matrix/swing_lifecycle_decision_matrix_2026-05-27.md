# Swing Lifecycle Decision Matrix 2026-05-27

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `135311`
- probe_rows: `132857`
- discovery_rows: `2454`
- raw_swing_event_count: `151166`
- ldm_consumed_event_count: `132857`
- ldm_event_coverage_rate: `0.878881`
- unmapped_swing_stage_counts: `{'market_regime_block': 9661, 'swing_probe_discarded': 7715, 'swing_probe_state_persisted': 312, 'swing_probe_state_restored': 130, 'swing_sim_buy_order_assumed_filled': 88, 'swing_sim_holding_started': 88, 'swing_sim_order_bundle_assumed_filled': 88, 'swing_same_symbol_loss_reentry_cooldowns_restored': 61, 'swing_reentry_counterfactual_after_loss': 57, 'swing_scale_in_micro_context_observed': 37, 'swing_sim_scale_in_order_assumed_filled': 37, 'swing_same_symbol_loss_reentry_blocked': 16, 'swing_probe_state_empty_overwrite_blocked': 8, 'swing_same_symbol_loss_reentry_cooldown': 6, 'swing_sim_sell_order_assumed_filled': 5}`
- sim_auto_candidate_count: `0`
- workorder_count: `9`
- swing_lifecycle_flow_bucket_count: `92`
- complete_flow_count: `7`
- incomplete_flow_count: `2607`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.002678`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `135311`
- bucket_count: `92`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`16` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`15` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`15` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`14` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`14` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `135151`
- bucket_count: `208`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BREAKOUT|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `2612`
- bucket_count: `54`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`12.677995`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`12.096912`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`8` ev=`11.037027`
- `mfe_mid|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`16` ev=`-3.0`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`15` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `25`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `2454`
- bucket_count: `1039`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`10.317317`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`5.878723`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`5.284402`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
