# Swing Lifecycle Decision Matrix 2026-06-23

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `16226`
- probe_rows: `6637`
- discovery_rows: `9589`
- raw_swing_event_count: `11460`
- ldm_consumed_event_count: `6637`
- ldm_event_coverage_rate: `0.579145`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 2549, 'market_regime_block': 1921, 'swing_reentry_counterfactual_after_loss': 94, 'swing_probe_state_restored': 67, 'swing_same_symbol_loss_reentry_cooldowns_restored': 57, 'swing_sim_order_bundle_assumed_filled': 43, 'swing_probe_state_persisted': 37, 'swing_same_symbol_loss_reentry_blocked': 31, 'swing_scale_in_micro_context_observed': 15, 'swing_same_symbol_loss_reentry_cooldown': 9}`
- sim_auto_candidate_count: `25`
- workorder_count: `27`
- swing_lifecycle_flow_bucket_count: `222`
- complete_flow_count: `905`
- incomplete_flow_count: `6893`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.116055`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `16226`
- bucket_count: `222`
- sim_auto_candidate_count: `25`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`25` ev=`7.45239`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`23` ev=`4.207718`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_190f958427|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`19` ev=`15.665682`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_554e260958|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`16` ev=`10.158612`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_1054c79628|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d` route=`sim_auto_approved` joined=`14` ev=`5.078225`
### entry_bucket_attribution
- source_row_count: `15277`
- bucket_count: `322`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `market_regime_prior_observed|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BOTTOM|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `8768`
- bucket_count: `61`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`15` ev=`19.756939`
- `mfe_low|mae_deep|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`4` ev=`-15.54526`
- `mfe_high|mae_flat|held_missing|fixed_5d_close|equal_notional|fixed_5d|-|-|-` route=`sim_auto_approved` joined=`15` ev=`13.819634`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`20` ev=`11.693142`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`10` ev=`10.560079`
### scale_in_bucket_attribution
- source_row_count: `24`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `9589`
- bucket_count: `2226`
- sim_auto_candidate_count: `0`
- workorder_count: `25`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Specialized Wholesale|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`4.987098`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|증권,창투|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|바이오_줄기세포치료제|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Semiconductor|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Other Financial Intermediation|NaN|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
