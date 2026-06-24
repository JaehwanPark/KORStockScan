# Conversion Lane - 2026-06-24

## Decision
- conversion candidates: `696`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `145`
- positive EV previous-policy natural match 0: `4`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `2`
- positive EV sample-floor unknown floor: `102`
- positive EV sample-floor related total: `104`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2, 'source_report_window': 102}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`2701` zero_count=`0` positive_count=`2701` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`14` counts=`{'canonical': 78, 'new_axis_pending_taxonomy': 14, 'unknown': 17}`
- active seed candidate validation: total=`2598` eligible=`2598` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`118` followup=`2480` matched=`1948` matched_true_without_seed_id=`0` unmatched=`650` new_entry_unmatched=`28` followup_unmatched=`622` eligible_without_seed_id=`650` without_seed_reasons=`{'followup_missing_parent_seed_id': 622, 'new_entry_without_seed_id': 28}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 622, 'taxonomy_pending_or_natural_no_match': 28}` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 28, 'scalp_sim_buy_order_virtual_pending': 28, 'scalp_sim_entry_submit_revalidation_warning': 27, 'scalp_sim_holding_started': 28, 'scalp_sim_panic_bottoming_entry_allowed': 4, 'scalp_sim_panic_level1_entry_observed': 22, 'scalp_sim_panic_scale_in_blocked': 410, 'scalp_sim_pre_submit_liquidity_guard_would_block': 12, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 16, 'scalp_sim_pre_submit_overbought_guard_would_pass': 28, 'scalp_sim_sell_order_assumed_filled': 19}` raw_without_seed_id=`650` eligible_followup_without_seed_id=`622` raw_followup_without_seed_id=`622`
- panic scale-in no-match: events=`1609` unique_sim_records=`91` missing_sim_record_id=`0` repeated_followup=`1518` status_counts=`{'matched': 57, 'no_match': 1609}` source_stage_counts=`{'blocked_ai_score': 422, 'first_ai_wait': 1135, 'scale_in': 52}`
- conversion candidate strategy scope: scalp=`47` swing=`648` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #2 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_86034b79d577`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_8a3588983be1`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8e98dd9cfa5`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8ed4dea4ee4`: sample_floor -> sample_floor
- #6 `swing_bucket_selection_discovery_arm_attribution_gap_fade_entry_risk_capped_fixed_5d_insurance_nan_diagnostic`: sample_floor -> sample_floor
- #7 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #8 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_435fd1c339`: sample_floor -> complete_parent_flow
- #9 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5ea568a2cc`: sample_floor -> complete_parent_flow
- #10 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b3df3092fc`: sample_floor -> complete_parent_flow
- #11 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dba225c97a`: sample_floor -> complete_parent_flow
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_cd9ad3c7af0f`: sample_floor -> sample_floor
- #13 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: sample_floor -> complete_parent_flow
- #14 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: sample_floor -> complete_parent_flow
- #15 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #16 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214`: sample_floor -> complete_parent_flow
- #17 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5`: sample_floor -> complete_parent_flow
- #18 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f2d9ce426031`: sample_floor -> sample_floor
- #19 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7d92990310`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
