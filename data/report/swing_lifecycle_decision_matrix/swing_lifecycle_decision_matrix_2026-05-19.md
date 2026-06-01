# Swing Lifecycle Decision Matrix 2026-05-19

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `294165`
- probe_rows: `294165`
- discovery_rows: `0`
- raw_swing_event_count: `302487`
- ldm_consumed_event_count: `294165`
- ldm_event_coverage_rate: `0.972488`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 7864, 'swing_reentry_counterfactual_after_loss': 388, 'swing_probe_state_persisted': 38, 'swing_scale_in_micro_context_observed': 11, 'swing_same_symbol_loss_reentry_cooldown': 9, 'swing_probe_state_restored': 7, 'swing_same_symbol_loss_reentry_cooldowns_restored': 5}`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- swing_lifecycle_flow_bucket_count: `14`
- complete_flow_count: `6`
- incomplete_flow_count: `23`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.206897`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['swing_strategy_discovery_sim_missing']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `294165`
- bucket_count: `14`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_2h_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`3` ev=`2.64`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`3` ev=`-3.403333`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-3.08`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_deep_neg_missing_ge_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-5.18`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_missing_2h_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`1` ev=`11.84`
### entry_bucket_attribution
- source_row_count: `294115`
- bucket_count: `13`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BREAKOUT|flat_up|75_84|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|75_84|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `41`
- bucket_count: `13`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `mfe_high|missing|2h_1d|kospi_trailing_start_take_profit|-|-|-|-|-` route=`source_only_keep_collecting` joined=`1` ev=`1.973333`
- `mfe_high|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-` route=`source_only_keep_collecting` joined=`1` ev=`1.973333`
- `mfe_deep_neg|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`-1.835`
- `mfe_neg|missing|2h_1d|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`5` ev=`-1.637`
- `mfe_neg|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`6` ev=`-1.4925`
### scale_in_bucket_attribution
- source_row_count: `22`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
