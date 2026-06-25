# Conversion Lane - 2026-06-25

## Decision
- conversion candidates: `695`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `135`
- positive EV previous-policy natural match 0: `7`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `103`
- positive EV sample-floor related total: `106`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 3, 'source_report_window': 103}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`2046` zero_count=`0` positive_count=`2046` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`14` counts=`{'canonical': 82, 'new_axis_pending_taxonomy': 14, 'unknown': 17}`
- active seed candidate validation: total=`1956` eligible=`1956` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`76` followup=`1880` matched=`1279` matched_true_without_seed_id=`0` unmatched=`677` new_entry_unmatched=`33` followup_unmatched=`644` eligible_without_seed_id=`677` without_seed_reasons=`{'followup_missing_parent_seed_id': 644, 'new_entry_without_seed_id': 33}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 644, 'taxonomy_pending_or_natural_no_match': 33}` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 33, 'scalp_sim_buy_order_virtual_pending': 33, 'scalp_sim_entry_ai_price_applied': 1, 'scalp_sim_entry_submit_revalidation_warning': 31, 'scalp_sim_holding_started': 33, 'scalp_sim_panic_bottoming_entry_allowed': 3, 'scalp_sim_panic_level1_entry_observed': 19, 'scalp_sim_panic_scale_in_blocked': 398, 'scalp_sim_pre_submit_liquidity_guard_would_block': 11, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 22, 'scalp_sim_pre_submit_overbought_guard_would_pass': 33, 'scalp_sim_scale_in_order_unfilled': 4, 'scalp_sim_sell_order_assumed_filled': 23}` raw_without_seed_id=`677` eligible_followup_without_seed_id=`644` raw_followup_without_seed_id=`644`
- panic scale-in no-match: events=`1245` unique_sim_records=`54` missing_sim_record_id=`0` repeated_followup=`1191` status_counts=`{'matched': 96, 'no_match': 1245}` source_stage_counts=`{'blocked_ai_score': 338, 'first_ai_wait': 907}`
- conversion candidate strategy scope: scalp=`45` swing=`649` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_we_04dd3ed862f2`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_37b6fa164d99`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_60c4c4c8cf4a`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_6801d1240a2d`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7e0794e7481b`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_86034b79d577`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_d509e3bd1627`: sample_floor -> sample_floor
- #14 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_fbf43185e883`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_3ca639695952`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_b5af9026adec`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconducto_724095770cd4`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
