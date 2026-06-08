# Swing Lifecycle Decision Matrix 2026-06-08

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `35540`
- probe_rows: `33874`
- discovery_rows: `1666`
- raw_swing_event_count: `51750`
- ldm_consumed_event_count: `33874`
- ldm_event_coverage_rate: `0.65457`
- unmapped_swing_stage_counts: `{'market_regime_block': 13053, 'swing_probe_discarded': 4586, 'swing_scale_in_micro_context_observed': 49, 'swing_probe_state_persisted': 44, 'swing_sim_order_bundle_assumed_filled': 36, 'swing_probe_state_restored': 31, 'swing_same_symbol_loss_reentry_cooldowns_restored': 30, 'swing_reentry_counterfactual_after_loss': 30, 'swing_same_symbol_loss_reentry_cooldown': 10, 'swing_same_symbol_loss_reentry_blocked': 7}`
- sim_auto_candidate_count: `1`
- workorder_count: `5`
- swing_lifecycle_flow_bucket_count: `65`
- complete_flow_count: `64`
- incomplete_flow_count: `1527`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.040226`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `3`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `35540`
- bucket_count: `65`
- sim_auto_candidate_count: `1`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:missing_missing_held_missing_kospi_trailing_start_take_profit` route=`sim_auto_approved` joined=`4` ev=`3.73`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_3bbc3ae5ef|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_s_b59dd3d98c` route=`source_only_keep_collecting` joined=`5` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_ge_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`4` ev=`-7.9875`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_3bbc3ae5ef|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`4` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `35431`
- bucket_count: `222`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `1699`
- bucket_count: `39`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_low|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`8` ev=`-3.0`
- `mfe_mid|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`-3.0`
- `mfe_deep_neg|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`-3.0`
- `mfe_neg|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`-3.0`
- `mfe_low|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `21`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `1666`
- bucket_count: `916`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|NaN|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`6.199921`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Banking and Savings Institutions|은행|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`4.176424`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|LCD_부품,LED,무선충전기관련주|MAIN` route=`source_only_keep_collecting` joined=`1` ev=`3.89671`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Insurance|보험_손해보험|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.678571`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.243943`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
