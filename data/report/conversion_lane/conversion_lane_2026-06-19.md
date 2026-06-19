# Conversion Lane - 2026-06-19

## Decision
- conversion candidates: `689`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `211`
- positive EV previous-policy natural match 0: `9`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `159`
- positive EV sample-floor related total: `162`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 3, 'source_report_window': 159}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`0` zero_count=`0` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`9` counts=`{'canonical': 75, 'new_axis_pending_taxonomy': 9, 'unknown': 17}`
- active seed candidate validation: total=`0` eligible=`0` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`0` followup=`0` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` missing_parent_stages=`{}` raw_without_seed_id=`0` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`0`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`53` swing=`635` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_079f38b7cea6`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32a6237321db`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_37b6fa164d99`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_86034b79d577`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a992ac4d9c63`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_ac21ef812543`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_c5b4b516e258`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insur_799158434bfb`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_insur_cd318fa7195b`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_5a1e662aabbb`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_b5af9026adec`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconducto_724095770cd4`: sample_floor -> sample_floor
- #19 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76`: sample_floor -> complete_parent_flow
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1d2a773521`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
