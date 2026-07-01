# Conversion Lane - 2026-07-01

## Decision
- conversion candidates: `693`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `122`
- positive EV previous-policy natural match 0: `5`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `2`
- positive EV sample-floor unknown floor: `88`
- positive EV sample-floor related total: `90`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2, 'source_report_window': 88}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`1549` zero_count=`0` positive_count=`1549` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`15` counts=`{'canonical': 95, 'new_axis_pending_taxonomy': 15, 'unknown': 16}`
- active seed candidate validation: total=`1346` eligible=`1346` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`61` followup=`1285` matched=`921` matched_true_without_seed_id=`0` unmatched=`425` new_entry_unmatched=`20` followup_unmatched=`405` eligible_without_seed_id=`425` without_seed_reasons=`{'followup_missing_parent_seed_id': 405, 'new_entry_without_seed_id': 20}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 405, 'taxonomy_pending_or_natural_no_match': 20}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 20, 'scalp_sim_buy_order_virtual_pending': 20, 'scalp_sim_entry_ai_price_applied': 10, 'scalp_sim_holding_started': 20, 'scalp_sim_panic_bottoming_entry_allowed': 3, 'scalp_sim_panic_level1_entry_observed': 12, 'scalp_sim_panic_scale_in_blocked': 275, 'scalp_sim_pre_submit_liquidity_guard_would_block': 2, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 18, 'scalp_sim_pre_submit_overbought_guard_would_pass': 20, 'scalp_sim_scale_in_order_unfilled': 1, 'scalp_sim_sell_order_assumed_filled': 4}` raw_without_seed_id=`425` eligible_followup_without_seed_id=`405` raw_followup_without_seed_id=`405`
- panic scale-in no-match: events=`1028` unique_sim_records=`45` missing_sim_record_id=`0` repeated_followup=`983` status_counts=`{'no_match': 1028}` source_stage_counts=`{'blocked_ai_score': 410, 'first_ai_wait': 467, 'scale_in': 151}`
- conversion candidate strategy scope: scalp=`39` swing=`653` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`PRICE_GUARD_DROUGHT` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_26508746e0b5`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_37b6fa164d99`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_6801d1240a2d`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_68b22c9a03ae`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a72594ac3c56`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #11 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_f95ca498b403`: sample_floor -> sample_floor
- #12 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_b5af9026adec`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconducto_724095770cd4`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_other_financial_intermediat_550a25892d04`: sample_floor -> sample_floor
- #17 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76`: sample_floor -> complete_parent_flow
- #18 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214`: sample_floor -> complete_parent_flow
- #19 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_435fd1c339`: sample_floor -> complete_parent_flow
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
