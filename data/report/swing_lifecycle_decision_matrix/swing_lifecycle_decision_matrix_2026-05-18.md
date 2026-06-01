# Swing Lifecycle Decision Matrix 2026-05-18

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `806081`
- probe_rows: `806081`
- discovery_rows: `0`
- raw_swing_event_count: `824161`
- ldm_consumed_event_count: `806081`
- ldm_event_coverage_rate: `0.978063`
- unmapped_swing_stage_counts: `{'swing_probe_discarded': 17469, 'swing_reentry_counterfactual_after_loss': 453, 'swing_probe_state_persisted': 104, 'swing_scale_in_micro_context_observed': 20, 'swing_same_symbol_loss_reentry_cooldown': 13, 'swing_probe_state_restored': 12, 'swing_same_symbol_loss_reentry_cooldowns_restored': 8, 'swing_probe_state_empty_overwrite_blocked': 1}`
- sim_auto_candidate_count: `0`
- workorder_count: `8`
- swing_lifecycle_flow_bucket_count: `26`
- complete_flow_count: `18`
- incomplete_flow_count: `34`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.346154`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['swing_strategy_discovery_sim_missing']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `806081`
- bucket_count: `26`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_ge_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`3` ev=`-1.54`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_lt_30m_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`3` ev=`-3.533333`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_ge_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-3.31`
- `entry=swing_entry:entry_bucket_attribution:missing_lt55_missing_kospi_ml|holding=swing_holding:holding_exit_bucket_attribution:missing_missing_held_missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_lt_30m_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`2` ev=`2.615`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_missing_ge_1d_kosdaq_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-2.59`
### entry_bucket_attribution
- source_row_count: `805967`
- bucket_count: `26`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `114`
- bucket_count: `17`
- sim_auto_candidate_count: `0`
- workorder_count: `8`
- `mfe_neg|missing|ge_1d|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`3` ev=`-1.62`
- `mfe_low|missing|lt_30m|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`10` ev=`-1.385`
- `mfe_low|missing|30m_2h|kospi_trailing_start_take_profit|-|-|-|-|-` route=`code_patch_required` joined=`5` ev=`1.328`
- `mfe_low|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-` route=`code_patch_required` joined=`16` ev=`1.318125`
- `mfe_low|missing|lt_30m|kospi_trailing_start_take_profit|-|-|-|-|-` route=`code_patch_required` joined=`9` ev=`1.310556`
### scale_in_bucket_attribution
- source_row_count: `38`
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
