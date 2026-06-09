# Conversion Lane - 2026-06-09

## Decision
- conversion candidates: `626`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `49`
- positive EV previous-policy natural match 0: `5`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `8`
- positive EV sample-floor unknown floor: `34`
- positive EV sample-floor related total: `42`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 8, 'source_report_window': 34}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`17427` zero_count=`0` positive_count=`17427` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`3` counts=`{'canonical': 24, 'new_axis_pending_taxonomy': 3, 'unknown': 23}`
- active seed candidate validation: total=`8315` new_entry=`180` followup=`8135` matched=`1848` matched_true_without_seed_id=`0` unmatched=`6467` new_entry_unmatched=`107` followup_unmatched=`6360` without_seed_id=`6467` followup_without_seed_id=`6360`
- panic scale-in no-match: events=`14850` unique_sim_records=`245` missing_sim_record_id=`0` repeated_followup=`14605` status_counts=`{'no_match': 14850}` source_stage_counts=`{'blocked_ai_score': 5553, 'first_ai_wait': 1163, 'scale_in': 8134}`
- conversion candidate strategy scope: scalp=`91` swing=`534` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_dba225c97a42`: sample_floor -> sample_floor
- #2 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_e59ff4f40eda`: sample_floor -> sample_floor
- #3 `active_arm_0c383886ae3c8de3`: key_lineage -> swing_active_arm_preopen_missing
- #4 `active_arm_342af4565cfdbf29`: key_lineage -> swing_active_arm_preopen_missing
- #5 `active_arm_7bc3260124b31b77`: key_lineage -> swing_active_arm_preopen_missing
- #6 `active_arm_83b3cc10ef194674`: key_lineage -> swing_active_arm_preopen_missing
- #7 `active_arm_d105ea417d1883a6`: key_lineage -> swing_active_arm_preopen_missing
- #8 `active_arm_d7bb9da5df1a251d`: key_lineage -> swing_active_arm_preopen_missing
- #9 `active_arm_da294c8705564eaf`: key_lineage -> swing_active_arm_preopen_missing
- #10 `active_seed_0629ba2d0f4dd524`: key_lineage -> key_lineage_preopen_missing
- #11 `active_seed_0747f150d4c2eab8`: key_lineage -> key_lineage_preopen_missing
- #12 `active_seed_07677c2e78c144df`: key_lineage -> key_lineage_preopen_missing
- #13 `active_seed_0a9736d86332c717`: key_lineage -> key_lineage_preopen_missing
- #14 `active_seed_0cae3a2115d07d28`: key_lineage -> key_lineage_preopen_missing
- #15 `active_seed_1096e7d8ada1ee8a`: key_lineage -> key_lineage_preopen_missing
- #16 `active_seed_109a6ab7807c9624`: key_lineage -> key_lineage_preopen_missing
- #17 `active_seed_1307cd5fa2e96df9`: key_lineage -> key_lineage_preopen_missing
- #18 `active_seed_24a139dfb60cb311`: key_lineage -> key_lineage_preopen_missing
- #19 `active_seed_31323d9e3795b722`: key_lineage -> key_lineage_preopen_missing
- #20 `active_seed_46465cc508b01988`: key_lineage -> key_lineage_preopen_missing

## Real Conversion Queue
- none
