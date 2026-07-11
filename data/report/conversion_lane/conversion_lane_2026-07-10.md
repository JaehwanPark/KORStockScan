# Conversion Lane - 2026-07-10

## Decision
- conversion candidates: `720`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `139`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `93`
- positive EV sample-floor related total: `96`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 3, 'source_report_window': 93}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`271` zero_count=`271` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`27` counts=`{'canonical': 97, 'new_axis_pending_taxonomy': 27, 'unknown': 16}`
- active seed candidate validation: total=`271` eligible=`271` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`38` followup=`233` matched=`8` matched_true_without_seed_id=`0` unmatched=`263` new_entry_unmatched=`37` followup_unmatched=`226` eligible_without_seed_id=`263` without_seed_reasons=`{'followup_missing_parent_seed_id': 226, 'new_entry_without_seed_id': 37}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 226, 'taxonomy_pending_or_natural_no_match': 37}` inferred_parent_seed_id=`8` inferred_stages=`{'scalp_sim_buy_order_assumed_filled': 1, 'scalp_sim_buy_order_virtual_pending': 1, 'scalp_sim_entry_ai_price_applied': 1, 'scalp_sim_entry_armed': 1, 'scalp_sim_holding_started': 1, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 1, 'scalp_sim_scale_in_order_unfilled': 1}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 37, 'scalp_sim_buy_order_virtual_pending': 37, 'scalp_sim_entry_ai_price_applied': 34, 'scalp_sim_holding_started': 37, 'scalp_sim_pre_submit_liquidity_guard_would_block': 12, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 25, 'scalp_sim_pre_submit_overbought_guard_would_pass': 37, 'scalp_sim_sell_order_assumed_filled': 7}` raw_without_seed_id=`271` eligible_followup_without_seed_id=`226` raw_followup_without_seed_id=`233`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`42` swing=`677` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_mae_stop_time_stop_10d_close_risk_c_e93e893cd115`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #5 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_risk_capped_fixed_10d`: sample_floor -> sample_floor
- #6 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_volatility_adjusted_fixed_10d`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32107919b18b`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7d9299031049`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f25078d70cbe`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f2c8f006300d`: sample_floor -> sample_floor
- #12 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_28e075b7575c`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_3dfc40c37c2c`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_build_d2f7389475f0`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_heavy_fb34ba47600d`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_2df153faea5b`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_f95ca498b403`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_044b6c899b11`: sample_floor -> sample_floor

## Real Conversion Queue
- none
