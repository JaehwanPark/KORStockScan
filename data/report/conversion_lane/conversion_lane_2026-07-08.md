# Conversion Lane - 2026-07-08

## Decision
- conversion candidates: `701`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `150`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `2`
- positive EV sample-floor unknown floor: `101`
- positive EV sample-floor related total: `103`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2, 'source_report_window': 101}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`1428` zero_count=`1428` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`23` counts=`{'canonical': 96, 'new_axis_pending_taxonomy': 23, 'unknown': 16}`
- active seed candidate validation: total=`1420` eligible=`1420` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`73` followup=`1347` matched=`1037` matched_true_without_seed_id=`0` unmatched=`383` new_entry_unmatched=`29` followup_unmatched=`354` eligible_without_seed_id=`383` without_seed_reasons=`{'followup_missing_parent_seed_id': 354, 'new_entry_without_seed_id': 29}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 354, 'taxonomy_pending_or_natural_no_match': 29}` inferred_parent_seed_id=`1037` inferred_stages=`{'scalp_sim_buy_order_assumed_filled': 44, 'scalp_sim_buy_order_virtual_pending': 44, 'scalp_sim_entry_ai_price_applied': 44, 'scalp_sim_entry_armed': 44, 'scalp_sim_holding_started': 44, 'scalp_sim_panic_bottoming_entry_allowed': 1, 'scalp_sim_panic_level1_entry_observed': 22, 'scalp_sim_panic_scale_in_blocked': 685, 'scalp_sim_pre_submit_liquidity_guard_would_block': 20, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 24, 'scalp_sim_pre_submit_overbought_guard_would_block': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 43, 'scalp_sim_scale_in_order_unfilled': 2, 'scalp_sim_sell_order_assumed_filled': 19}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 29, 'scalp_sim_buy_order_virtual_pending': 29, 'scalp_sim_entry_ai_price_applied': 27, 'scalp_sim_holding_started': 29, 'scalp_sim_panic_level1_entry_observed': 12, 'scalp_sim_panic_scale_in_blocked': 157, 'scalp_sim_pre_submit_liquidity_guard_would_block': 11, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 18, 'scalp_sim_pre_submit_overbought_guard_would_block': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 28, 'scalp_sim_scale_in_order_assumed_filled': 1, 'scalp_sim_scale_in_order_unfilled': 5, 'scalp_sim_sell_order_assumed_filled': 7}` raw_without_seed_id=`1420` eligible_followup_without_seed_id=`354` raw_followup_without_seed_id=`1347`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 842}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`29` swing=`671` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_w_b4cd7a061381`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_mae_stop_time_stop_10d_close_risk_c_e93e893cd115`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #5 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_volatility_adjusted_fixed_10d`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32b59151de7b`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3ff5b203d481`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_74ef3de393ed`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_d509e3bd1627`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_da5b17ed0a1b`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8ed4dea4ee4`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f25078d70cbe`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_real_estate_e5a8439ce3f0`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_wholesale_o_a64b7a7411b7`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_3dfc40c37c2c`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_c40c18ab90cd`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_build_d2f7389475f0`: sample_floor -> sample_floor

## Real Conversion Queue
- none
