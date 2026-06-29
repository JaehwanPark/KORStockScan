# Conversion Lane - 2026-06-29

## Decision
- conversion candidates: `681`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `112`
- positive EV previous-policy natural match 0: `3`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `6`
- positive EV sample-floor unknown floor: `83`
- positive EV sample-floor related total: `89`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 6, 'source_report_window': 83}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`2398` zero_count=`2398` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`16` counts=`{'canonical': 85, 'new_axis_pending_taxonomy': 16, 'unknown': 17}`
- active seed candidate validation: total=`2285` eligible=`2285` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`48` followup=`2237` matched=`0` matched_true_without_seed_id=`0` unmatched=`2285` new_entry_unmatched=`48` followup_unmatched=`2237` eligible_without_seed_id=`2285` without_seed_reasons=`{'followup_missing_parent_seed_id': 2237, 'new_entry_without_seed_id': 48}` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 2237, 'taxonomy_pending_or_natural_no_match': 48}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`1364` missing_parent_stages=`{'scalp_sim_buy_order_assumed_filled': 48, 'scalp_sim_buy_order_virtual_pending': 48, 'scalp_sim_entry_ai_price_applied': 19, 'scalp_sim_entry_submit_revalidation_warning': 18, 'scalp_sim_holding_started': 48, 'scalp_sim_panic_level1_entry_observed': 17, 'scalp_sim_panic_scale_in_blocked': 1915, 'scalp_sim_pre_submit_liquidity_guard_would_block': 12, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 36, 'scalp_sim_pre_submit_overbought_guard_would_pass': 48, 'scalp_sim_scale_in_order_unfilled': 2, 'scalp_sim_sell_order_assumed_filled': 26}` raw_without_seed_id=`2285` eligible_followup_without_seed_id=`2237` raw_followup_without_seed_id=`2237`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 2018}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`32` swing=`648` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_we_04dd3ed862f2`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_we_7043014629c6`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_26508746e0b5`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32a6237321db`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_37b6fa164d99`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_56e63809289a`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_68b22c9a03ae`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_6e73fea6f579`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7480cc41ef57`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7e0794e7481b`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_8de0a8a2530a`: sample_floor -> sample_floor
- #14 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #15 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #16 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e59ff4f40eda`: sample_floor -> sample_floor
- #17 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_f2c8f006300d`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_b5af9026adec`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconducto_724095770cd4`: sample_floor -> sample_floor

## Real Conversion Queue
- none
