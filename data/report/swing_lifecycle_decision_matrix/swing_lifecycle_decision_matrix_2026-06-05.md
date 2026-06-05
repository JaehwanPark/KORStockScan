# Swing Lifecycle Decision Matrix 2026-06-05

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `76232`
- probe_rows: `75250`
- discovery_rows: `982`
- raw_swing_event_count: `103673`
- ldm_consumed_event_count: `75250`
- ldm_event_coverage_rate: `0.72584`
- unmapped_swing_stage_counts: `{'market_regime_block': 23589, 'swing_probe_discarded': 4408, 'swing_scale_in_micro_context_observed': 186, 'swing_probe_state_persisted': 55, 'swing_probe_state_restored': 53, 'swing_same_symbol_loss_reentry_cooldowns_restored': 51, 'swing_reentry_counterfactual_after_loss': 46, 'swing_sim_order_bundle_assumed_filled': 15, 'swing_same_symbol_loss_reentry_cooldown': 14, 'swing_same_symbol_loss_reentry_blocked': 6}`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- swing_lifecycle_flow_bucket_count: `26`
- complete_flow_count: `8`
- incomplete_flow_count: `997`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.00796`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `3`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `76232`
- bucket_count: `26`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_ge_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-3.5`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_neg_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`2` ev=`-3.565`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-3.07`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_missing_ge_1d_kospi_trailing_start_take_profit` route=`source_only_keep_collecting` joined=`1` ev=`3.31`
- `entry=entry:missing|holding=holding:missing|scale_in=swing_scale_in:scale_in_bucket_attribution:avg_down_instrumentation_gap_swing_dynamic_allowed_market|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_missing_2h_1d_kospi_regime_stop_loss` route=`source_only_keep_collecting` joined=`1` ev=`-3.03`
### entry_bucket_attribution
- source_row_count: `76163`
- bucket_count: `122`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `-|-|-|missing|missing|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|lt55|missing|KOSPI_ML|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `-|-|-|missing|missing|missing|-|-|-` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down_large|75_84|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `1060`
- bucket_count: `24`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `mfe_low|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`10` ev=`-1.4415`
- `missing|missing|held_missing|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`4` ev=`-1.38375`
- `mfe_low|missing|30m_2h|kospi_trailing_start_take_profit|-|-|-|-|-` route=`code_patch_required` joined=`4` ev=`1.29125`
- `mfe_low|missing|held_missing|kospi_trailing_start_take_profit|-|-|-|-|-` route=`code_patch_required` joined=`6` ev=`1.279167`
- `mfe_low|missing|30m_2h|kospi_regime_stop_loss|-|-|-|-|-` route=`code_patch_required` joined=`5` ev=`-1.268`
### scale_in_bucket_attribution
- source_row_count: `25`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `982`
- bucket_count: `695`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Other Chemical Products|-|RUNNER` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `bottom_rebound_signal_close_retest_limit_entry|risk_capped|fixed_10d|Manufacture of Other Chemical Products|-|RUNNER` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `bottom_rebound_next_open_entry|equal_notional|fixed_10d|Manufacture of Sewn Wearing Apparel, Except Fur Apparel|의복_OEM|RUNNER` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Manufacture of Other Non-metallic Mineral Products|-|RUNNER` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `bottom_rebound_atr_pullback_limit_entry|volatility_adjusted|mae_stop_time_stop|Wholesale of Construction Materials, Hardware and Heating and Air Conditioning Equipment|-|RUNNER` route=`source_only_keep_collecting` joined=`0` ev=`0.0`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
