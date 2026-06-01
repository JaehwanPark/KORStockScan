# Swing Lifecycle Decision Matrix 2026-05-28

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `63103`
- probe_rows: `59899`
- discovery_rows: `3204`
- raw_swing_event_count: `78602`
- ldm_consumed_event_count: `59899`
- ldm_event_coverage_rate: `0.762054`
- unmapped_swing_stage_counts: `{'market_regime_block': 14954, 'swing_probe_discarded': 3458, 'swing_probe_state_persisted': 60, 'swing_probe_state_restored': 43, 'swing_same_symbol_loss_reentry_cooldowns_restored': 32, 'swing_sim_buy_order_assumed_filled': 27, 'swing_sim_holding_started': 27, 'swing_sim_order_bundle_assumed_filled': 27, 'swing_reentry_counterfactual_after_loss': 27, 'swing_scale_in_micro_context_observed': 16, 'swing_sim_scale_in_order_assumed_filled': 16, 'swing_same_symbol_loss_reentry_cooldown': 7, 'swing_same_symbol_loss_reentry_blocked': 7, 'swing_sim_sell_order_assumed_filled': 2}`
- sim_auto_candidate_count: `0`
- workorder_count: `17`
- swing_lifecycle_flow_bucket_count: `69`
- complete_flow_count: `10`
- incomplete_flow_count: `3234`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.003083`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `63103`
- bucket_count: `69`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`49` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`37` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`28` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`20` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`18` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `62840`
- bucket_count: `205`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|BREAKOUT|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `3249`
- bucket_count: `63`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`3` ev=`36.985252`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`9` ev=`14.94003`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`9` ev=`12.546744`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`11.870726`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`10.749032`
### scale_in_bucket_attribution
- source_row_count: `8`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `3204`
- bucket_count: `1300`
- sim_auto_candidate_count: `0`
- workorder_count: `12`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Telecommunication and Broadcasting Apparatuses|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`17.482359`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`11.777436`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`5.878723`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`5.284402`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
