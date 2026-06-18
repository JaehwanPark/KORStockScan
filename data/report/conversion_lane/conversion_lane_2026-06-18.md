# Conversion Lane - 2026-06-18

## Decision
- conversion candidates: `707`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `209`
- positive EV previous-policy natural match 0: `10`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `6`
- positive EV sample-floor unknown floor: `159`
- positive EV sample-floor related total: `165`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 6, 'source_report_window': 159}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`16658` zero_count=`0` positive_count=`16658` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`9` counts=`{'canonical': 75, 'new_axis_pending_taxonomy': 9, 'unknown': 17}`
- active seed candidate validation: total=`10449` eligible=`10449` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`193` followup=`10256` matched=`10015` matched_true_without_seed_id=`0` unmatched=`434` new_entry_unmatched=`9` followup_unmatched=`425` eligible_without_seed_id=`434` without_seed_reasons=`{'followup_missing_parent_seed_id': 425, 'new_entry_without_seed_id': 9}` raw_without_seed_id=`434` eligible_followup_without_seed_id=`425` raw_followup_without_seed_id=`425`
- panic scale-in no-match: events=`6977` unique_sim_records=`136` missing_sim_record_id=`0` repeated_followup=`6841` status_counts=`{'matched': 7053, 'no_match': 6977}` source_stage_counts=`{'blocked_ai_score': 871, 'first_ai_wait': 6106}`
- conversion candidate strategy scope: scalp=`67` swing=`639` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_fixed_5d_close_risk_capped_fixed_5d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_1d2a77352168`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_395eb9924904`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_435fd1c3391a`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_5ea568a2cc33`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_7d8473110896`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_80055598bbf1`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_954cc23e9135`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_dbcdc8c83952`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e8e98dd9cfa5`: sample_floor -> sample_floor
- #14 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_eb0c1a5747c7`: sample_floor -> sample_floor
- #15 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_fbf43185e883`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_c7e25aaffb95`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_passe_f7fc8347feee`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_gap_fade_entry_risk_capped_fixed_5d_insurance_nan_diagnostic`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_electronic_c_d09d91772573`: sample_floor -> sample_floor
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_310f349c63`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
