# Conversion Lane - 2026-07-03

## Decision
- conversion candidates: `705`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `145`
- positive EV previous-policy natural match 0: `5`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `2`
- positive EV sample-floor unknown floor: `101`
- positive EV sample-floor related total: `103`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2, 'source_report_window': 101}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`1614` zero_count=`0` positive_count=`1614` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`18` counts=`{'canonical': 96, 'new_axis_pending_taxonomy': 18, 'unknown': 17}`
- active seed candidate validation: total=`1557` eligible=`1557` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`46` followup=`1511` matched=`1218` matched_true_without_seed_id=`0` unmatched=`339` new_entry_unmatched=`14` followup_unmatched=`325` eligible_without_seed_id=`339` without_seed_reasons=`{'followup_missing_parent_seed_id': 325, 'new_entry_without_seed_id': 14}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 325, 'taxonomy_pending_or_natural_no_match': 14}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 14, 'scalp_sim_buy_order_virtual_pending': 14, 'scalp_sim_entry_ai_price_applied': 11, 'scalp_sim_holding_started': 14, 'scalp_sim_panic_bottoming_entry_allowed': 1, 'scalp_sim_panic_level1_entry_observed': 8, 'scalp_sim_panic_scale_in_blocked': 228, 'scalp_sim_pre_submit_liquidity_guard_would_block': 8, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 6, 'scalp_sim_pre_submit_overbought_guard_would_pass': 14, 'scalp_sim_sell_order_assumed_filled': 7}` raw_without_seed_id=`339` eligible_followup_without_seed_id=`325` raw_followup_without_seed_id=`325`
- panic scale-in no-match: events=`1234` unique_sim_records=`32` missing_sim_record_id=`0` repeated_followup=`1202` status_counts=`{'no_match': 1234}` source_stage_counts=`{'blocked_ai_score': 315, 'first_ai_wait': 878, 'scale_in': 41}`
- conversion candidate strategy scope: scalp=`35` swing=`669` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`UPSTREAM_AI_THRESHOLD` matches=`['LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_fixed_10d_close_risk_capped_fixed_10d`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_26508746e0b5`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_56e63809289a`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_60c4c4c8cf4a`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_74ef3de393ed`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a72594ac3c56`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_cd936e85635e`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f25078d70cbe`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_3dfc40c37c2c`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_build_d2f7389475f0`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_heavy_fb34ba47600d`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_f95ca498b403`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_b5af9026adec`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconducto_724095770cd4`: sample_floor -> sample_floor

## Real Conversion Queue
- none
