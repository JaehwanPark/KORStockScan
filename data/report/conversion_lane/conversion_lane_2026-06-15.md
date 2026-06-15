# Conversion Lane - 2026-06-15

## Decision
- conversion candidates: `636`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `159`
- positive EV previous-policy natural match 0: `6`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `126`
- positive EV sample-floor related total: `129`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 3, 'source_report_window': 126}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`14399` zero_count=`8165` positive_count=`6234` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`9` counts=`{'canonical': 70, 'new_axis_pending_taxonomy': 9, 'unknown': 17}`
- active seed candidate validation: total=`10678` eligible=`1509` not_match_eligible=`9169` not_match_eligible_reasons=`{'diagnostic_followup_without_seed_context': 9169}` new_entry=`204` followup=`10474` matched=`9` matched_true_without_seed_id=`0` unmatched=`1500` new_entry_unmatched=`203` followup_unmatched=`1297` eligible_without_seed_id=`1500` raw_without_seed_id=`10669` eligible_followup_without_seed_id=`1297` raw_followup_without_seed_id=`10466`
- panic scale-in no-match: events=`4421` unique_sim_records=`81` missing_sim_record_id=`0` repeated_followup=`4340` status_counts=`{'matched': 1115, 'no_match': 4421, 'policy_disabled': 6560}` source_stage_counts=`{'blocked_ai_score': 3282, 'first_ai_wait': 1, 'scale_in': 1138}`
- conversion candidate strategy scope: scalp=`44` swing=`591` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_w_b4cd7a061381`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32a6237321db`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_3b6dc9288520`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_fbf43185e883`: sample_floor -> sample_floor
- #7 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_b99781db765f`: sample_floor -> sample_floor
- #8 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_d06300a0cecf`: sample_floor -> sample_floor
- #9 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_26ca74e077`: sample_floor -> complete_parent_flow
- #10 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: sample_floor -> complete_parent_flow
- #11 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b0984ff4fa`: sample_floor -> complete_parent_flow
- #12 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c515f99b98`: sample_floor -> complete_parent_flow
- #13 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_we_04dd3ed862f2`: sample_floor -> sample_floor
- #14 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7e0794e748`: sample_floor -> complete_parent_flow
- #15 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_1d398f64abec`: sample_floor -> sample_floor
- #16 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5`: sample_floor -> complete_parent_flow
- #17 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e59ff4f40eda`: sample_floor -> sample_floor
- #18 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_we_7043014629c6`: sample_floor -> sample_floor
- #19 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a1c9198050ec`: sample_floor -> sample_floor
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7480cc41ef`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
