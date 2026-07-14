# Conversion Lane - 2026-07-14

## Decision
- conversion candidates: `701`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `126`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `81`
- positive EV sample-floor related total: `81`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`source_report_window` window_counts=`{'source_report_window': 81}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`632` zero_count=`632` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`37` counts=`{'canonical': 102, 'new_axis_pending_taxonomy': 37, 'unknown': 13}`
- active seed candidate validation: total=`632` eligible=`632` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`22` followup=`610` matched=`0` matched_true_without_seed_id=`0` unmatched=`632` new_entry_unmatched=`22` followup_unmatched=`610` eligible_without_seed_id=`632` without_seed_reasons=`{'followup_missing_parent_seed_id': 610, 'new_entry_without_seed_id': 22}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 610, 'taxonomy_pending_or_natural_no_match': 22}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 22, 'scalp_sim_buy_order_virtual_pending': 22, 'scalp_sim_entry_ai_price_applied': 22, 'scalp_sim_entry_submit_revalidation_warning': 1, 'scalp_sim_holding_started': 22, 'scalp_sim_panic_bottoming_entry_allowed': 1, 'scalp_sim_panic_level1_entry_observed': 18, 'scalp_sim_panic_scale_in_blocked': 458, 'scalp_sim_pre_submit_liquidity_guard_would_block': 8, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 14, 'scalp_sim_pre_submit_overbought_guard_would_pass': 22}` raw_without_seed_id=`632` eligible_followup_without_seed_id=`610` raw_followup_without_seed_id=`610`
- panic scale-in no-match: events=`458` unique_sim_records=`18` missing_sim_record_id=`0` repeated_followup=`440` status_counts=`{'no_match': 458}` source_stage_counts=`{'blocked_ai_score': 162, 'first_ai_wait': 296}`
- conversion candidate strategy scope: scalp=`29` swing=`671` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_w_b4cd7a061381`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_mae_stop_time_stop_10d_close_risk_c_e93e893cd115`: sample_floor -> sample_floor
- #5 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #6 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_risk_capped_fixed_10d`: sample_floor -> sample_floor
- #7 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_volatility_adjusted_fixed_10d`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32b59151de7b`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_6801d1240a2d`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_c5b4b516e258`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_dba225c97a42`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8ed4dea4ee4`: sample_floor -> sample_floor
- #14 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f25078d70cbe`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_real_estate_e5a8439ce3f0`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_wholesale_o_a64b7a7411b7`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_3dfc40c37c2c`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_c40c18ab90cd`: sample_floor -> sample_floor

## Real Conversion Queue
- none
