# Conversion Lane - 2026-07-06

## Decision
- conversion candidates: `708`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `146`
- positive EV previous-policy natural match 0: `2`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `98`
- positive EV sample-floor related total: `99`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1, 'source_report_window': 98}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`955` zero_count=`0` positive_count=`955` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`19` counts=`{'canonical': 95, 'new_axis_pending_taxonomy': 19, 'unknown': 16}`
- active seed candidate validation: total=`882` eligible=`882` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`67` followup=`815` matched=`546` matched_true_without_seed_id=`0` unmatched=`336` new_entry_unmatched=`21` followup_unmatched=`315` eligible_without_seed_id=`336` without_seed_reasons=`{'followup_missing_parent_seed_id': 315, 'new_entry_without_seed_id': 21}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 315, 'taxonomy_pending_or_natural_no_match': 21}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 21, 'scalp_sim_buy_order_virtual_pending': 21, 'scalp_sim_entry_ai_price_applied': 19, 'scalp_sim_holding_started': 21, 'scalp_sim_panic_level1_entry_observed': 15, 'scalp_sim_panic_scale_in_blocked': 167, 'scalp_sim_pre_submit_liquidity_guard_would_block': 11, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 10, 'scalp_sim_pre_submit_overbought_guard_would_pass': 21, 'scalp_sim_scale_in_order_assumed_filled': 1, 'scalp_sim_scale_in_order_unfilled': 4, 'scalp_sim_sell_order_assumed_filled': 4}` raw_without_seed_id=`336` eligible_followup_without_seed_id=`315` raw_followup_without_seed_id=`315`
- panic scale-in no-match: events=`347` unique_sim_records=`32` missing_sim_record_id=`0` repeated_followup=`315` status_counts=`{'matched': 23, 'no_match': 347}` source_stage_counts=`{'blocked_ai_score': 172, 'first_ai_wait': 175}`
- conversion candidate strategy scope: scalp=`40` swing=`667` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`UPSTREAM_AI_THRESHOLD` matches=`['LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_volatility_adjusted_fixed_10d`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32b59151de7b`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3ff5b203d481`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_56e63809289a`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_5884b57cb95f`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8ed4dea4ee4`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f25078d70cbe`: sample_floor -> sample_floor
- #12 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_build_d2f7389475f0`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_23ae9be172f5`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_f95ca498b403`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_gap_fade_entry_risk_capped_fixed_5d_insurance_nan_diagnostic`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electric_lam_672a0f93e4b0`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_instruments_b3e92bf187e8`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_other_financial_intermediat_550a25892d04`: sample_floor -> sample_floor

## Real Conversion Queue
- none
