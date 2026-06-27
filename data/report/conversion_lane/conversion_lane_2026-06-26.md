# Conversion Lane - 2026-06-26

## Decision
- conversion candidates: `692`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `126`
- positive EV previous-policy natural match 0: `9`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `119`
- positive EV sample-floor related total: `120`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1, 'source_report_window': 119}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`2402` zero_count=`0` positive_count=`2402` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`16` counts=`{'canonical': 84, 'new_axis_pending_taxonomy': 16, 'unknown': 17}`
- active seed candidate validation: total=`2290` eligible=`2290` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`79` followup=`2211` matched=`1133` matched_true_without_seed_id=`0` unmatched=`1157` new_entry_unmatched=`33` followup_unmatched=`1124` eligible_without_seed_id=`1157` without_seed_reasons=`{'followup_missing_parent_seed_id': 1124, 'new_entry_without_seed_id': 33}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 1124, 'taxonomy_pending_or_natural_no_match': 33}` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 33, 'scalp_sim_buy_order_virtual_pending': 33, 'scalp_sim_entry_submit_revalidation_warning': 33, 'scalp_sim_holding_started': 33, 'scalp_sim_panic_bottoming_entry_allowed': 4, 'scalp_sim_panic_level1_entry_observed': 28, 'scalp_sim_panic_scale_in_blocked': 866, 'scalp_sim_pre_submit_liquidity_guard_would_block': 13, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 20, 'scalp_sim_pre_submit_overbought_guard_would_pass': 33, 'scalp_sim_scale_in_order_unfilled': 5, 'scalp_sim_sell_order_assumed_filled': 23}` raw_without_seed_id=`1157` eligible_followup_without_seed_id=`1124` raw_followup_without_seed_id=`1124`
- panic scale-in no-match: events=`1667` unique_sim_records=`68` missing_sim_record_id=`0` repeated_followup=`1599` status_counts=`{'no_match': 1667}` source_stage_counts=`{'blocked_ai_score': 993, 'first_ai_wait': 590, 'scale_in': 84}`
- conversion candidate strategy scope: scalp=`42` swing=`649` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_6e73fea6f579`: sample_floor -> sample_floor
- #2 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_8a3588983be1`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_dba225c97a42`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8e98dd9cfa5`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8ed4dea4ee4`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_eb0c1a5747c7`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f2c8f006300d`: sample_floor -> sample_floor
- #8 `swing_bucket_selection_discovery_arm_attribution_gap_fade_entry_risk_capped_fixed_5d_insurance_nan_diagnostic`: sample_floor -> sample_floor
- #9 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_435fd1c339`: sample_floor -> sample_floor
- #10 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5ea568a2cc`: sample_floor -> sample_floor
- #11 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b3df3092fc`: sample_floor -> sample_floor
- #12 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7d92990310`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_c5b4b516e258`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #15 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7480cc41ef57`: sample_floor -> sample_floor
- #16 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_we_7043014629c6`: sample_floor -> sample_floor
- #17 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214`: sample_floor -> sample_floor
- #18 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #19 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_w_b4cd7a061381`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_insurance_diagnostic`: sample_floor -> sample_floor

## Real Conversion Queue
- none
