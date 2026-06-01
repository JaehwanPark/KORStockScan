# Swing Lifecycle Decision Matrix 2026-06-01

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `96638`
- probe_rows: `91483`
- discovery_rows: `5155`
- raw_swing_event_count: `96819`
- ldm_consumed_event_count: `91483`
- ldm_event_coverage_rate: `0.944887`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 5132, 'swing_probe_state_persisted': 58, 'swing_probe_state_restored': 51, 'swing_same_symbol_loss_reentry_cooldowns_restored': 41, 'swing_reentry_counterfactual_after_loss': 25, 'swing_scale_in_micro_context_observed': 15, 'swing_same_symbol_loss_reentry_cooldown': 5, 'swing_sim_order_bundle_assumed_filled': 5, 'swing_same_symbol_loss_reentry_blocked': 4}`
- sim_auto_candidate_count: `7`
- workorder_count: `30`
- swing_lifecycle_flow_bucket_count: `116`
- complete_flow_count: `321`
- incomplete_flow_count: `4211`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.07083`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `96638`
- bucket_count: `116`
- sim_auto_candidate_count: `7`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`16` ev=`35.451567`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_weig_04dd3ed862` route=`sim_auto_approved` joined=`7` ev=`8.146256`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weigh_f216b9c539` route=`sim_auto_approved` joined=`6` ev=`3.867408`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`5` ev=`11.59379`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_cd796a93d8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_we_9fe6398193` route=`sim_auto_approved` joined=`5` ev=`25.612119`
### entry_bucket_attribution
- source_row_count: `96257`
- bucket_count: `288`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_gatekeeper_reject|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `4906`
- bucket_count: `39`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`28` ev=`34.443653`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`18.014125`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`15` ev=`10.770326`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`16` ev=`8.747189`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`8` ev=`6.705081`
### scale_in_bucket_attribution
- source_row_count: `30`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `5155`
- bucket_count: `1456`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Telecommunication and Broadcasting Apparatuses|반도체_생산|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`9.678934`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Precious and Non-ferrous Metals|비철금속주|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Other Transport Equipment|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
