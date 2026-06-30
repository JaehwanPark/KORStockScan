# Conversion Lane - 2026-06-30

## Decision
- conversion candidates: `695`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `111`
- positive EV previous-policy natural match 0: `3`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `82`
- positive EV sample-floor related total: `83`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1, 'source_report_window': 82}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`1728` zero_count=`0` positive_count=`1728` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`17` counts=`{'canonical': 90, 'new_axis_pending_taxonomy': 17, 'unknown': 17}`
- active seed candidate validation: total=`1711` eligible=`1711` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`84` followup=`1627` matched=`657` matched_true_without_seed_id=`0` unmatched=`1054` new_entry_unmatched=`45` followup_unmatched=`1009` eligible_without_seed_id=`1054` without_seed_reasons=`{'followup_missing_parent_seed_id': 1009, 'new_entry_without_seed_id': 45}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 1009, 'taxonomy_pending_or_natural_no_match': 45}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 45, 'scalp_sim_buy_order_virtual_pending': 45, 'scalp_sim_entry_ai_price_applied': 18, 'scalp_sim_entry_submit_revalidation_warning': 2, 'scalp_sim_holding_started': 45, 'scalp_sim_panic_bottoming_entry_allowed': 8, 'scalp_sim_panic_level1_entry_observed': 27, 'scalp_sim_panic_scale_in_blocked': 723, 'scalp_sim_pre_submit_liquidity_guard_would_block': 7, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 38, 'scalp_sim_pre_submit_overbought_guard_would_pass': 45, 'scalp_sim_sell_order_assumed_filled': 6}` raw_without_seed_id=`1054` eligible_followup_without_seed_id=`1009` raw_followup_without_seed_id=`1009`
- panic scale-in no-match: events=`1048` unique_sim_records=`50` missing_sim_record_id=`0` repeated_followup=`998` status_counts=`{'matched': 27, 'no_match': 1048}` source_stage_counts=`{'blocked_ai_score': 882, 'first_ai_wait': 166}`
- conversion candidate strategy scope: scalp=`46` swing=`648` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`PRICE_GUARD_DROUGHT` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #2 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_60c4c4c8cf4a`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7480cc41ef57`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_8a3588983be1`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_dba225c97a42`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8e98dd9cfa5`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8ed4dea4ee4`: sample_floor -> sample_floor
- #10 `swing_bucket_selection_discovery_arm_attribution_gap_fade_entry_risk_capped_fixed_5d_insurance_nan_diagnostic`: sample_floor -> sample_floor
- #11 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_other_financial_intermediat_550a25892d04`: sample_floor -> sample_floor
- #12 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_435fd1c339`: sample_floor -> complete_parent_flow
- #13 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5ea568a2cc`: sample_floor -> complete_parent_flow
- #14 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b3df3092fc`: sample_floor -> complete_parent_flow
- #15 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_eb0c1a5747`: sample_floor -> complete_parent_flow
- #16 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #17 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_d27ece90a1a8`: sample_floor -> sample_floor
- #18 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214`: sample_floor -> complete_parent_flow
- #19 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_56e63809289a`: sample_floor -> sample_floor
- #20 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor

## Real Conversion Queue
- none
