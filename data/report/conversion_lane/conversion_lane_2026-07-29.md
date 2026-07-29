# Conversion Lane - 2026-07-29

## Decision
- conversion candidates: `25`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `2`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `1`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`61` zero_count=`61` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`45` counts=`{'canonical': 116, 'new_axis_pending_taxonomy': 45, 'unknown': 13}`
- active seed candidate validation: total=`61` eligible=`0` not_match_eligible=`61` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 61}` new_entry=`3` followup=`58` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`61` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`58`
- panic scale-in no-match: events=`14` unique_sim_records=`3` missing_sim_record_id=`0` repeated_followup=`11` status_counts=`{'no_match': 14}` source_stage_counts=`{'blocked_ai_score': 14}`
- conversion candidate strategy scope: scalp=`24` swing=`0` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `key_lineage`; top blocker by count: `key_lineage`
- top LDM bucket blocker: `key_lineage`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`LATENCY_DROUGHT` matches=`['LATENCY_DROUGHT']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `active_arm_07b7bc397f7a9d64`: key_lineage -> swing_active_arm_preopen_missing
- #2 `active_arm_0e6d07fa10a5b582`: key_lineage -> swing_active_arm_preopen_missing
- #3 `active_arm_0fcffe09b9b7096c`: key_lineage -> swing_active_arm_preopen_missing
- #4 `active_arm_15f74aa27eef743d`: key_lineage -> swing_active_arm_preopen_missing
- #5 `active_arm_1661ca30f0d594fd`: key_lineage -> swing_active_arm_preopen_missing
- #6 `active_arm_292c648e73675368`: key_lineage -> swing_active_arm_preopen_missing
- #7 `active_arm_2c44a9b1dd392eb3`: key_lineage -> swing_active_arm_preopen_missing
- #8 `active_arm_2d256010e69684c1`: key_lineage -> swing_active_arm_preopen_missing
- #9 `active_arm_3034ae45da8fefbc`: key_lineage -> swing_active_arm_preopen_missing
- #10 `active_arm_368b41a18c7e3a5e`: key_lineage -> swing_active_arm_preopen_missing
- #11 `active_arm_400bb07e38eb1ab2`: key_lineage -> swing_active_arm_preopen_missing
- #12 `active_arm_400f801d872d0781`: key_lineage -> swing_active_arm_preopen_missing
- #13 `active_arm_431cb98e1d4adfce`: key_lineage -> swing_active_arm_preopen_missing
- #14 `active_arm_449bf7156fc91f04`: key_lineage -> swing_active_arm_preopen_missing
- #15 `active_arm_50c137ab85107620`: key_lineage -> swing_active_arm_preopen_missing
- #16 `active_arm_518e85a70ac730e3`: key_lineage -> swing_active_arm_preopen_missing
- #17 `active_arm_52e8c1f2d0e05882`: key_lineage -> swing_active_arm_preopen_missing
- #18 `active_arm_57c8b15599062480`: key_lineage -> swing_active_arm_preopen_missing
- #19 `active_arm_594203d8ae056b29`: key_lineage -> swing_active_arm_preopen_missing
- #20 `active_arm_5ed5448f4e3ccb60`: key_lineage -> swing_active_arm_preopen_missing

## Real Conversion Queue
- none
