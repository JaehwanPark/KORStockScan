# Swing Lifecycle Decision Matrix 2026-06-09

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `57420`
- probe_rows: `55143`
- discovery_rows: `2277`
- raw_swing_event_count: `60612`
- ldm_consumed_event_count: `55143`
- ldm_event_coverage_rate: `0.90977`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 5229, 'swing_scale_in_micro_context_observed': 70, 'swing_probe_state_restored': 52, 'swing_probe_state_persisted': 48, 'swing_same_symbol_loss_reentry_cooldowns_restored': 38, 'swing_reentry_counterfactual_after_loss': 15, 'swing_sim_order_bundle_assumed_filled': 13, 'swing_same_symbol_loss_reentry_cooldown': 3, 'swing_same_symbol_loss_reentry_blocked': 1}`
- sim_auto_candidate_count: `0`
- workorder_count: `9`
- swing_lifecycle_flow_bucket_count: `88`
- complete_flow_count: `193`
- incomplete_flow_count: `1726`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.100573`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `57420`
- bucket_count: `88`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_aa5acd00c4|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_volatility_adjusted_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_mae_mid_held_missing_mae_stop_touched_volatility_adjusted_mae_287e28c1d7` route=`source_only_keep_collecting` joined=`17` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_aa5acd00c4|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_volatility_adjusted_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_volatility_adjusted_mae_2e05582a7d` route=`source_only_keep_collecting` joined=`14` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_s_b59dd3d98c` route=`source_only_keep_collecting` joined=`14` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_3bbc3ae5ef|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_s_b59dd3d98c` route=`source_only_keep_collecting` joined=`12` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3692b81ae8|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_s_b59dd3d98c` route=`source_only_keep_collecting` joined=`10` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `57170`
- bucket_count: `219`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BOTTOM|flat_up|75_84|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `2157`
- bucket_count: `44`
- sim_auto_candidate_count: `0`
- workorder_count: `3`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`7.411996`
- `mfe_deep_neg|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`47` ev=`-3.0`
- `mfe_neg|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`20` ev=`-3.0`
- `mfe_neg|mae_mid|held_missing|mae_stop_touched|volatility_adjusted|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`17` ev=`-3.0`
- `mfe_low|mae_mid|held_missing|mae_stop_touched|volatility_adjusted|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`14` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `27`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `2277`
- bucket_count: `1031`
- sim_auto_candidate_count: `0`
- workorder_count: `6`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Chemicals|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Banking and Savings Institutions|은행|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`6.259083`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`3.145079`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Specialized Wholesale|자원개발 E&P|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.184266`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.074866`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
