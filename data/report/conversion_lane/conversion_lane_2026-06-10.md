# Conversion Lane - 2026-06-10

## Decision
- conversion candidates: `721`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `81`
- positive EV previous-policy natural match 0: `5`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `6`
- positive EV sample-floor unknown floor: `61`
- positive EV sample-floor related total: `67`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 6, 'source_report_window': 61}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`17585` zero_count=`17585` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`5` counts=`{'canonical': 53, 'new_axis_pending_taxonomy': 5, 'unknown': 19}`
- active seed candidate validation: total=`1276` new_entry=`79` followup=`1197` matched=`0` matched_true_without_seed_id=`0` unmatched=`1276` new_entry_unmatched=`79` followup_unmatched=`1197` without_seed_id=`1276` followup_without_seed_id=`1197`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_disabled': 13434}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`136` swing=`584` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop_confidence_w_bdea57b1fe95`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_we_04dd3ed862f2`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32a6237321db`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_68b22c9a03ae`: sample_floor -> sample_floor
- #5 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_ccc3dfa9dbb9`: sample_floor -> sample_floor
- #6 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e59ff4f40eda`: sample_floor -> sample_floor
- #7 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_banki_8fbf0e91f50c`: sample_floor -> sample_floor
- #8 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop_confidence_we_7043014629c6`: sample_floor -> sample_floor
- #9 `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: sample_floor -> complete_parent_flow
- #10 `active_arm_0c383886ae3c8de3`: key_lineage -> swing_active_arm_preopen_missing
- #11 `active_arm_342af4565cfdbf29`: key_lineage -> swing_active_arm_preopen_missing
- #12 `active_arm_7bc3260124b31b77`: key_lineage -> swing_active_arm_preopen_missing
- #13 `active_arm_83b3cc10ef194674`: key_lineage -> swing_active_arm_preopen_missing
- #14 `active_arm_d105ea417d1883a6`: key_lineage -> swing_active_arm_preopen_missing
- #15 `active_arm_d7bb9da5df1a251d`: key_lineage -> swing_active_arm_preopen_missing
- #16 `active_arm_da294c8705564eaf`: key_lineage -> swing_active_arm_preopen_missing
- #17 `active_seed_03c539e6527cdda2`: key_lineage -> key_lineage_preopen_missing
- #18 `active_seed_0629ba2d0f4dd524`: key_lineage -> key_lineage_preopen_missing
- #19 `active_seed_0747f150d4c2eab8`: key_lineage -> key_lineage_preopen_missing
- #20 `active_seed_07677c2e78c144df`: key_lineage -> key_lineage_preopen_missing

## Real Conversion Queue
- none
