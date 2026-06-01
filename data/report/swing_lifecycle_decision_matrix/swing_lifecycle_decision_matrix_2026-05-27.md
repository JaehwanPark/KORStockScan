# Swing Lifecycle Decision Matrix 2026-05-27

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `135607`
- probe_rows: `133075`
- discovery_rows: `2532`
- raw_swing_event_count: `151166`
- ldm_consumed_event_count: `133075`
- ldm_event_coverage_rate: `0.880324`
- unmapped_swing_stage_counts: `{'market_regime_block': 9661, 'swing_probe_discarded': 7715, 'swing_probe_state_persisted': 312, 'swing_probe_state_restored': 130, 'swing_sim_order_bundle_assumed_filled': 88, 'swing_same_symbol_loss_reentry_cooldowns_restored': 61, 'swing_reentry_counterfactual_after_loss': 57, 'swing_scale_in_micro_context_observed': 37, 'swing_same_symbol_loss_reentry_blocked': 16, 'swing_probe_state_empty_overwrite_blocked': 8, 'swing_same_symbol_loss_reentry_cooldown': 6}`
- sim_auto_candidate_count: `1`
- workorder_count: `6`
- swing_lifecycle_flow_bucket_count: `50`
- complete_flow_count: `43`
- incomplete_flow_count: `2431`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.017381`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `135607`
- bucket_count: `50`
- sim_auto_candidate_count: `1`
- workorder_count: `0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_a930b0706a|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_confidence_weighted_trailing_after_mfe|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_weig_7043014629` route=`sim_auto_approved` joined=`3` ev=`10.445393`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_bottom_discovery_ga_895f9502b5|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`3` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`3` ev=`-3.0`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:missing_missing_held_missing_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-2.805`
- `entry=swing_entry:entry_bucket_attribution:swing_strategy_discovery_sim_v1_no_block_observed_breakout_discovery_293bb70a1d|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing_risk_capped_mae_stop_time_stop|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched_risk_capped_mae_stop_time_stop` route=`source_only_keep_collecting` joined=`2` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `135481`
- bucket_count: `189`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BREAKOUT|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `2744`
- bucket_count: `32`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`5` ev=`10.541281`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|confidence_weighted|trailing_after_mfe|-|-|-` route=`sim_auto_approved` joined=`4` ev=`10.067166`
- `mfe_low|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`9` ev=`-3.0`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`-3.0`
- `mfe_mid|mae_deep|held_missing|mae_stop_touched|risk_capped|mae_stop_time_stop|-|-|-` route=`sim_auto_approved` joined=`3` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `62`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `2532`
- bucket_count: `1039`
- sim_auto_candidate_count: `0`
- workorder_count: `1`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`15.430652`
- `breakout_confirm_entry|risk_capped|mae_stop_time_stop|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`12.779014`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`7.410206`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Telecommunication and Broadcasting Apparatuses|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`5.197994`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
