# Conversion Lane - 2026-06-08

## Decision
- conversion candidates: `4`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `0`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`source_report_window` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`30821` zero_count=`21658` positive_count=`9163` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`0` counts=`{'unknown': 31}`
- active seed candidate validation: total=`6991` new_entry=`130` followup=`6861` matched=`0` matched_true_without_seed_id=`0` unmatched=`6991` new_entry_unmatched=`130` followup_unmatched=`6861` without_seed_id=`6991` followup_without_seed_id=`6861`
- panic scale-in no-match: events=`9042` unique_sim_records=`109` missing_sim_record_id=`0` repeated_followup=`8933` status_counts=`{'matched': 16637, 'no_match': 9042}` source_stage_counts=`{'blocked_ai_score': 1523, 'first_ai_wait': 4288, 'scale_in': 3231}`
- conversion candidate strategy scope: scalp=`4` swing=`0` unscoped=`0`
- bounded real canary requestable: `0`
- top blocker ranked: `key_lineage`; top blocker by count: `key_lineage`
- top LDM bucket blocker: `key_lineage`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`PRICE_GUARD_DROUGHT` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `active_arm_0c383886ae3c8de3`: key_lineage -> swing_active_arm_preopen_missing
- #2 `active_arm_342af4565cfdbf29`: key_lineage -> swing_active_arm_preopen_missing
- #3 `active_arm_790e3894639690bd`: key_lineage -> swing_active_arm_preopen_missing
- #4 `active_arm_7bc3260124b31b77`: key_lineage -> swing_active_arm_preopen_missing
- #5 `active_arm_83b3cc10ef194674`: key_lineage -> swing_active_arm_preopen_missing
- #6 `active_arm_d105ea417d1883a6`: key_lineage -> swing_active_arm_preopen_missing
- #7 `active_arm_d7bb9da5df1a251d`: key_lineage -> swing_active_arm_preopen_missing
- #8 `active_arm_da294c8705564eaf`: key_lineage -> swing_active_arm_preopen_missing
- #9 `active_seed_0a9736d86332c717`: key_lineage -> key_lineage_preopen_missing
- #10 `active_seed_0cae3a2115d07d28`: key_lineage -> key_lineage_preopen_missing
- #11 `active_seed_1096e7d8ada1ee8a`: key_lineage -> key_lineage_preopen_missing
- #12 `active_seed_109a6ab7807c9624`: key_lineage -> key_lineage_preopen_missing
- #13 `active_seed_1307cd5fa2e96df9`: key_lineage -> key_lineage_preopen_missing
- #14 `active_seed_24a139dfb60cb311`: key_lineage -> key_lineage_preopen_missing
- #15 `active_seed_46465cc508b01988`: key_lineage -> key_lineage_preopen_missing
- #16 `active_seed_760c98186c8de610`: key_lineage -> key_lineage_preopen_missing
- #17 `active_seed_7cf1c198fc1e5246`: key_lineage -> key_lineage_preopen_missing
- #18 `active_seed_afa0c4f1bdf63001`: key_lineage -> key_lineage_preopen_missing
- #19 `active_seed_b99a2dea7aac2a83`: key_lineage -> key_lineage_preopen_missing
- #20 `active_seed_bef67812d7545625`: key_lineage -> key_lineage_preopen_missing

## Real Conversion Queue
- none
