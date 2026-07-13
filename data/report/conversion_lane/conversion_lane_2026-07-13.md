# Conversion Lane - 2026-07-13

## Decision
- conversion candidates: `707`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `132`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `90`
- positive EV sample-floor related total: `90`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`source_report_window` window_counts=`{'source_report_window': 90}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`594` zero_count=`594` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`35` counts=`{'canonical': 93, 'new_axis_pending_taxonomy': 35, 'unknown': 16}`
- active seed candidate validation: total=`594` eligible=`594` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`15` followup=`579` matched=`0` matched_true_without_seed_id=`0` unmatched=`594` new_entry_unmatched=`15` followup_unmatched=`579` eligible_without_seed_id=`594` without_seed_reasons=`{'followup_missing_parent_seed_id': 579, 'new_entry_without_seed_id': 15}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 579, 'taxonomy_pending_or_natural_no_match': 15}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 15, 'scalp_sim_buy_order_virtual_pending': 15, 'scalp_sim_entry_ai_price_applied': 13, 'scalp_sim_holding_started': 15, 'scalp_sim_panic_level1_entry_observed': 14, 'scalp_sim_panic_scale_in_blocked': 468, 'scalp_sim_pre_submit_liquidity_guard_would_block': 5, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 10, 'scalp_sim_pre_submit_overbought_guard_would_pass': 15, 'scalp_sim_sell_order_assumed_filled': 9}` raw_without_seed_id=`594` eligible_followup_without_seed_id=`579` raw_followup_without_seed_id=`579`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 468}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`30` swing=`676` unscoped=`1`
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
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_74ef3de393ed`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f25078d70cbe`: sample_floor -> sample_floor
- #12 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_28e075b7575c`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_3dfc40c37c2c`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_build_d2f7389475f0`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_heavy_fb34ba47600d`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_2df153faea5b`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_95ca38dcdcfa`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_f95ca498b403`: sample_floor -> sample_floor

## Real Conversion Queue
- none
