# Conversion Lane - 2026-06-23

## Decision
- conversion candidates: `710`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `181`
- positive EV previous-policy natural match 0: `4`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `5`
- positive EV sample-floor unknown floor: `158`
- positive EV sample-floor related total: `163`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 5, 'source_report_window': 158}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`3601` zero_count=`0` positive_count=`3601` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`12` counts=`{'canonical': 78, 'new_axis_pending_taxonomy': 12, 'unknown': 17}`
- active seed candidate validation: total=`2992` eligible=`2992` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`178` followup=`2814` matched=`2521` matched_true_without_seed_id=`0` unmatched=`471` new_entry_unmatched=`26` followup_unmatched=`445` eligible_without_seed_id=`471` without_seed_reasons=`{'followup_missing_parent_seed_id': 445, 'new_entry_without_seed_id': 26}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 445, 'taxonomy_pending_or_natural_no_match': 26}` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 26, 'scalp_sim_buy_order_virtual_pending': 26, 'scalp_sim_entry_submit_revalidation_warning': 25, 'scalp_sim_holding_started': 26, 'scalp_sim_panic_bottoming_entry_allowed': 1, 'scalp_sim_panic_level1_entry_observed': 23, 'scalp_sim_panic_scale_in_blocked': 245, 'scalp_sim_pre_submit_liquidity_guard_would_block': 18, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 8, 'scalp_sim_pre_submit_overbought_guard_would_pass': 26, 'scalp_sim_sell_order_assumed_filled': 21}` raw_without_seed_id=`471` eligible_followup_without_seed_id=`445` raw_followup_without_seed_id=`445`
- panic scale-in no-match: events=`1461` unique_sim_records=`158` missing_sim_record_id=`0` repeated_followup=`1303` status_counts=`{'matched': 294, 'no_match': 1461}` source_stage_counts=`{'blocked_ai_score': 428, 'first_ai_wait': 1033}`
- conversion candidate strategy scope: scalp=`46` swing=`663` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_4e8af5577b53`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_86034b79d577`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #8 `swing_bucket_selection_discovery_arm_attribution_gap_fade_entry_risk_capped_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #9 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_b5af9026adec`: sample_floor -> sample_floor
- #10 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #11 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconducto_724095770cd4`: sample_floor -> sample_floor
- #12 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #13 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76`: sample_floor -> sample_floor
- #14 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214`: sample_floor -> sample_floor
- #15 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_435fd1c339`: sample_floor -> sample_floor
- #16 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_56e6380928`: sample_floor -> complete_parent_flow
- #17 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: sample_floor -> sample_floor
- #18 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_9a16bc8153`: sample_floor -> sample_floor
- #19 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ac21ef8125`: sample_floor -> complete_parent_flow
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d27ece90a1`: sample_floor -> sample_floor

## Real Conversion Queue
- none
