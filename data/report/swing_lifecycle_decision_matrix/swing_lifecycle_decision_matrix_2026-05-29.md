# Swing Lifecycle Decision Matrix 2026-05-29

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `63838`
- probe_rows: `59752`
- discovery_rows: `4086`
- raw_swing_event_count: `63539`
- ldm_consumed_event_count: `59752`
- ldm_event_coverage_rate: `0.940399`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 3350, 'swing_probe_state_restored': 67, 'swing_probe_state_persisted': 60, 'swing_same_symbol_loss_reentry_cooldowns_restored': 58, 'swing_sim_buy_order_assumed_filled': 44, 'swing_sim_holding_started': 44, 'swing_sim_order_bundle_assumed_filled': 44, 'swing_reentry_counterfactual_after_loss': 44, 'swing_scale_in_micro_context_observed': 25, 'swing_sim_scale_in_order_assumed_filled': 25, 'swing_same_symbol_loss_reentry_blocked': 12, 'swing_sim_sell_order_assumed_filled': 8, 'swing_same_symbol_loss_reentry_cooldown': 6}`
- sim_auto_candidate_count: `8`
- workorder_count: `17`
- swing_lifecycle_flow_bucket_count: `106`
- complete_flow_count: `234`
- incomplete_flow_count: `3420`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.064039`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `63838`
- bucket_count: `106`
- sim_auto_candidate_count: `8`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_trailing_after_mfe_stop_confidence_weig_cadb5f3b06` route=`sim_auto_approved` joined=`5` ev=`2.889375`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weigh_f216b9c539` route=`sim_auto_approved` joined=`5` ev=`3.343281`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_trailing_after_mfe_stop_confidence_weig_cadb5f3b06` route=`sim_auto_approved` joined=`4` ev=`3.185272`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`3` ev=`11.754871`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_wei_b4cd7a0613` route=`sim_auto_approved` joined=`3` ev=`18.488637`
### entry_bucket_attribution
- source_row_count: `63574`
- bucket_count: `286`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|BOTTOM|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `3910`
- bucket_count: `31`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`3` ev=`36.985252`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`9` ev=`14.94003`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`9` ev=`12.546744`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`11.870726`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`10.749032`
### scale_in_bucket_attribution
- source_row_count: `11`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `4086`
- bucket_count: `1356`
- sim_auto_candidate_count: `0`
- workorder_count: `15`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`5.878723`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`5.284402`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
