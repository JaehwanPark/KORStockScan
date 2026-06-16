# Conversion Lane - 2026-06-16

## Decision
- conversion candidates: `662`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `178`
- positive EV previous-policy natural match 0: `7`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `4`
- positive EV sample-floor unknown floor: `140`
- positive EV sample-floor related total: `144`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 4, 'source_report_window': 140}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`6139` zero_count=`0` positive_count=`6139` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`10` counts=`{'canonical': 71, 'new_axis_pending_taxonomy': 10, 'unknown': 17}`
- active seed candidate validation: total=`3567` eligible=`3567` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`181` followup=`3386` matched=`3503` matched_true_without_seed_id=`0` unmatched=`64` new_entry_unmatched=`7` followup_unmatched=`57` eligible_without_seed_id=`64` without_seed_reasons=`{'followup_missing_parent_seed_id': 57, 'new_entry_without_seed_id': 7}` raw_without_seed_id=`64` eligible_followup_without_seed_id=`57` raw_followup_without_seed_id=`57`
- panic scale-in no-match: events=`3836` unique_sim_records=`133` missing_sim_record_id=`0` repeated_followup=`3703` status_counts=`{'matched': 191, 'no_match': 3836}` source_stage_counts=`{'blocked_ai_score': 1656, 'first_ai_wait': 304, 'scale_in': 1876}`
- conversion candidate strategy scope: scalp=`51` swing=`610` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop_confidence_w_b4cd7a061381`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_032d9962d4aa`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_21d4fe8f3461`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_22424ac7f8e0`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_a72594ac3c56`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_ca7cad92a07c`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e59ff4f40eda`: sample_floor -> sample_floor
- #9 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_c7e25aaffb95`: sample_floor -> sample_floor
- #10 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_passe_f7fc8347feee`: sample_floor -> sample_floor
- #11 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_0ff904dc07`: sample_floor -> complete_parent_flow
- #12 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: sample_floor -> complete_parent_flow
- #13 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7480cc41ef`: sample_floor -> complete_parent_flow
- #14 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c515f99b98`: sample_floor -> complete_parent_flow
- #15 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c5b4b516e2`: sample_floor -> complete_parent_flow
- #16 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dba225c97a`: sample_floor -> complete_parent_flow
- #17 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_fbf43185e8`: sample_floor -> complete_parent_flow
- #18 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: sample_floor -> complete_parent_flow
- #19 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_310f349c63`: sample_floor -> complete_parent_flow
- #20 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b0984ff4fa`: sample_floor -> complete_parent_flow

## Real Conversion Queue
- none
