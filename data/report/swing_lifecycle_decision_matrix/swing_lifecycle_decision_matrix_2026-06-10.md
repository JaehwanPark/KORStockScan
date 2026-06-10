# Swing Lifecycle Decision Matrix 2026-06-10

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `57471`
- probe_rows: `54421`
- discovery_rows: `3050`
- raw_swing_event_count: `75972`
- ldm_consumed_event_count: `54421`
- ldm_event_coverage_rate: `0.71633`
- unmapped_swing_stage_counts: `{'market_regime_block': 16182, 'swing_probe_discarded': 5017, 'swing_sim_order_bundle_assumed_filled': 74, 'swing_reentry_counterfactual_after_loss': 64, 'swing_probe_state_restored': 48, 'swing_scale_in_micro_context_observed': 47, 'swing_same_symbol_loss_reentry_cooldowns_restored': 44, 'swing_probe_state_persisted': 37, 'swing_same_symbol_loss_reentry_blocked': 18, 'swing_same_symbol_loss_reentry_cooldown': 14, 'swing_probe_state_empty_overwrite_blocked': 6}`
- sim_auto_candidate_count: `3`
- workorder_count: `13`
- swing_lifecycle_flow_bucket_count: `137`
- complete_flow_count: `253`
- incomplete_flow_count: `2341`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.097533`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `57471`
- bucket_count: `137`
- sim_auto_candidate_count: `3`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_3516b99175|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weigh_f216b9c539` route=`sim_auto_approved` joined=`3` ev=`3.115107`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_wei_b4cd7a0613` route=`sim_auto_approved` joined=`3` ev=`10.477788`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_nan_discovery_gap_u_3730eea9ce|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_low_held_missing_trailing_after_mfe_stop_confidence_weigh_20a6523afe` route=`sim_auto_approved` joined=`3` ev=`2.980416`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_aa5acd00c4|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_volatility_adjusted_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_mid_held_missing_mae_stop_touched_volatility_adjusted_mae_2e05582a7d` route=`source_only_keep_collecting` joined=`19` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_middle_discovery_ga_24b5dde5ab|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_s_b59dd3d98c` route=`source_only_keep_collecting` joined=`12` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `57155`
- bucket_count: `271`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `2920`
- bucket_count: `45`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`18.695765`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`3` ev=`16.493939`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`10.611433`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`6` ev=`8.888413`
- `mfe_mid|mae_low|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`3.066256`
### scale_in_bucket_attribution
- source_row_count: `41`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `3050`
- bucket_count: `1255`
- sim_auto_candidate_count: `0`
- workorder_count: `9`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Banking and Savings Institutions|은행|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`11.110342`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Chemicals|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Basic Iron and Steel|조선_해양플랜트기자재|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Specialized Wholesale|자원개발 E&P|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`6.771225`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
