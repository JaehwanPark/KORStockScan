# Conversion Lane - 2026-06-17

## Decision
- conversion candidates: `634`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `179`
- positive EV previous-policy natural match 0: `8`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `7`
- positive EV sample-floor unknown floor: `136`
- positive EV sample-floor related total: `143`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 7, 'source_report_window': 136}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`1628` zero_count=`0` positive_count=`1628` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`9` counts=`{'canonical': 73, 'new_axis_pending_taxonomy': 9, 'unknown': 17}`
- active seed candidate validation: total=`1010` eligible=`1010` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`117` followup=`893` matched=`380` matched_true_without_seed_id=`0` unmatched=`630` new_entry_unmatched=`74` followup_unmatched=`556` eligible_without_seed_id=`630` without_seed_reasons=`{'followup_missing_parent_seed_id': 556, 'new_entry_without_seed_id': 74}` raw_without_seed_id=`630` eligible_followup_without_seed_id=`556` raw_followup_without_seed_id=`556`
- panic scale-in no-match: events=`136` unique_sim_records=`20` missing_sim_record_id=`0` repeated_followup=`116` status_counts=`{'matched': 9, 'no_match': 136}` source_stage_counts=`{'blocked_ai_score': 53, 'first_ai_wait': 30, 'scale_in': 53}`
- conversion candidate strategy scope: scalp=`51` swing=`582` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #2 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_56e63809289a`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_68b22c9a03ae`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_86034b79d577`: sample_floor -> sample_floor
- #6 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: sample_floor -> complete_parent_flow
- #7 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5`: sample_floor -> complete_parent_flow
- #8 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: sample_floor -> complete_parent_flow
- #9 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_310f349c63`: sample_floor -> complete_parent_flow
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_c5b4b516e258`: sample_floor -> sample_floor
- #11 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_32a6237321`: sample_floor -> complete_parent_flow
- #12 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_3ca639695952`: sample_floor -> sample_floor
- #14 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7d92990310`: sample_floor -> complete_parent_flow
- #15 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_624410f340e0`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_b99781db765f`: sample_floor -> sample_floor
- #17 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dba225c97a`: sample_floor -> complete_parent_flow
- #18 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b0984ff4fa`: sample_floor -> complete_parent_flow
- #19 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_w_b4cd7a061381`: sample_floor -> sample_floor
- #20 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_we_7043014629c6`: sample_floor -> sample_floor

## Real Conversion Queue
- none
