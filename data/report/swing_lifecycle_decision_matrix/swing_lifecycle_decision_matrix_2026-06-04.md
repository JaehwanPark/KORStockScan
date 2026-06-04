# Swing Lifecycle Decision Matrix 2026-06-04

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `18542`
- probe_rows: `18142`
- discovery_rows: `400`
- raw_swing_event_count: `19023`
- ldm_consumed_event_count: `18142`
- ldm_event_coverage_rate: `0.953688`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 818, 'swing_sim_order_bundle_assumed_filled': 17, 'swing_probe_state_persisted': 15, 'swing_probe_state_restored': 9, 'swing_reentry_counterfactual_after_loss': 8, 'swing_scale_in_micro_context_observed': 6, 'swing_same_symbol_loss_reentry_cooldowns_restored': 5, 'swing_same_symbol_loss_reentry_blocked': 2, 'swing_same_symbol_loss_reentry_cooldown': 1}`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- swing_lifecycle_flow_bucket_count: `15`
- complete_flow_count: `2`
- incomplete_flow_count: `412`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.004831`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `3`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `18542`
- bucket_count: `15`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:missing_missing_held_missing_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`1` ev=`2.5`
- `entry=swing_entry:entry_bucket_attribution:missing_missing_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:missing_missing_held_missing_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-3.07`
- `entry=entry:missing|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=exit:missing` route=`source_only_keep_collecting` joined=`0` ev=`None`
- `entry=entry:missing|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_10d|scale_in=scale_in:none|exit=exit:missing` route=`source_only_keep_collecting` joined=`0` ev=`None`
- `entry=entry:missing|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_equal_notional_fixed_5d|scale_in=scale_in:none|exit=exit:missing` route=`source_only_keep_collecting` joined=`0` ev=`None`
### entry_bucket_attribution
- source_row_count: `18533`
- bucket_count: `62`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|normal|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|65_74|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `420`
- bucket_count: `10`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `missing|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`-0.768333`
- `missing|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-` route=`source_only_keep_collecting` joined=`1` ev=`0.416667`
- `missing|missing|held_missing|-|-|-|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `missing|missing|held_missing|-|confidence_weighted|trailing_after_mfe|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `missing|missing|held_missing|-|risk_capped|mae_stop_time_stop|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### scale_in_bucket_attribution
- source_row_count: `6`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `400`
- bucket_count: `336`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|스마트 그리드|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Iron and Steel|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Specialized Wholesale|자원개발 E&P|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Motor Vehicles and Engines for Motor Vehicles|그린카_하이브리드카/전기차|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`0` ev=`0.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
