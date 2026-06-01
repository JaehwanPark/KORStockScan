# Swing Lifecycle Decision Matrix 2026-05-28

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `63307`
- probe_rows: `59971`
- discovery_rows: `3336`
- raw_swing_event_count: `78602`
- ldm_consumed_event_count: `59971`
- ldm_event_coverage_rate: `0.76297`
- unmapped_swing_stage_counts: `{'market_regime_block': 14954, 'swing_probe_discarded': 3458, 'swing_probe_state_persisted': 60, 'swing_probe_state_restored': 43, 'swing_same_symbol_loss_reentry_cooldowns_restored': 32, 'swing_sim_order_bundle_assumed_filled': 27, 'swing_reentry_counterfactual_after_loss': 27, 'swing_scale_in_micro_context_observed': 16, 'swing_same_symbol_loss_reentry_cooldown': 7, 'swing_same_symbol_loss_reentry_blocked': 7}`
- sim_auto_candidate_count: `1`
- workorder_count: `6`
- swing_lifecycle_flow_bucket_count: `68`
- complete_flow_count: `73`
- incomplete_flow_count: `3156`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.022608`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `63307`
- bucket_count: `68`
- sim_auto_candidate_count: `1`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`3` ev=`10.403888`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_9459438419|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_missing_2h_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`3` ev=`3.436667`
### entry_bucket_attribution
- source_row_count: `63185`
- bucket_count: `186`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|BREAKOUT|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `3344`
- bucket_count: `42`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`18.003206`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`13.363055`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`9.25424`
- `mfe_mid|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`4.288176`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`12` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `24`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `3336`
- bucket_count: `1300`
- sim_auto_candidate_count: `0`
- workorder_count: `1`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`13.060994`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Telecommunication and Broadcasting Apparatuses|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`9.424761`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Plastic Products|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`12.097551`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
