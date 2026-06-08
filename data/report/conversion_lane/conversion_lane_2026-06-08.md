# Conversion Lane - 2026-06-08

## Decision
- conversion candidates: `667`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `46`
- positive EV previous-policy natural match 0: `8`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `4`
- positive EV sample-floor unknown floor: `33`
- positive EV sample-floor related total: `37`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 4, 'source_report_window': 33}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`20078` zero_count=`10829` positive_count=`9249` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`0` counts=`{'unknown': 31}`
- active seed candidate validation: total=`4043` new_entry=`74` followup=`3969` matched=`44` matched_true_without_seed_id=`0` unmatched=`3999` new_entry_unmatched=`72` followup_unmatched=`3927` without_seed_id=`3999` followup_without_seed_id=`3927`
- panic scale-in no-match: events=`5506` unique_sim_records=`121` missing_sim_record_id=`0` repeated_followup=`5385` status_counts=`{'matched': 11089, 'no_match': 5506}` source_stage_counts=`{'blocked_ai_score': 898, 'first_ai_wait': 2343, 'scale_in': 2265}`
- conversion candidate strategy scope: scalp=`160` swing=`506` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`PRICE_GUARD_DROUGHT` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #2 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_da5b17ed0a1b`: sample_floor -> sample_floor
- #3 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_dba225c97a42`: sample_floor -> sample_floor
- #4 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_39442155c048`: sample_floor -> sample_floor
- #5 `active_arm_0c383886ae3c8de3`: key_lineage -> swing_active_arm_preopen_missing
- #6 `active_arm_342af4565cfdbf29`: key_lineage -> swing_active_arm_preopen_missing
- #7 `active_arm_790e3894639690bd`: key_lineage -> swing_active_arm_preopen_missing
- #8 `active_arm_7bc3260124b31b77`: key_lineage -> swing_active_arm_preopen_missing
- #9 `active_arm_83b3cc10ef194674`: key_lineage -> swing_active_arm_preopen_missing
- #10 `active_arm_d105ea417d1883a6`: key_lineage -> swing_active_arm_preopen_missing
- #11 `active_arm_d7bb9da5df1a251d`: key_lineage -> swing_active_arm_preopen_missing
- #12 `active_arm_da294c8705564eaf`: key_lineage -> swing_active_arm_preopen_missing
- #13 `active_seed_0a9736d86332c717`: key_lineage -> key_lineage_preopen_missing
- #14 `active_seed_0cae3a2115d07d28`: key_lineage -> key_lineage_preopen_missing
- #15 `active_seed_1096e7d8ada1ee8a`: key_lineage -> key_lineage_preopen_missing
- #16 `active_seed_109a6ab7807c9624`: key_lineage -> key_lineage_preopen_missing
- #17 `active_seed_1307cd5fa2e96df9`: key_lineage -> key_lineage_preopen_missing
- #18 `active_seed_24a139dfb60cb311`: key_lineage -> key_lineage_preopen_missing
- #19 `active_seed_46465cc508b01988`: key_lineage -> key_lineage_preopen_missing
- #20 `active_seed_760c98186c8de610`: key_lineage -> key_lineage_preopen_missing

## Real Conversion Queue
- none
