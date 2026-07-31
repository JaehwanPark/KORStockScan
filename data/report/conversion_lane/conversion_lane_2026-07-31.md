# Conversion Lane - 2026-07-31

## Decision
- conversion candidates: `30`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `1`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`130` zero_count=`130` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`45` counts=`{'canonical': 117, 'new_axis_pending_taxonomy': 45, 'unknown': 13}`
- active seed candidate validation: total=`113` eligible=`0` not_match_eligible=`113` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 113}` new_entry=`5` followup=`108` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`113` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`108`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`29` swing=`0` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `key_lineage`; top blocker by count: `key_lineage`
- top LDM bucket blocker: `key_lineage`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `active_arm_0180070855c2b7e5`: key_lineage -> swing_active_arm_preopen_missing
- #2 `active_arm_02727d57924e4971`: key_lineage -> swing_active_arm_preopen_missing
- #3 `active_arm_05b90b0c95e7ab43`: key_lineage -> swing_active_arm_preopen_missing
- #4 `active_arm_07b7bc397f7a9d64`: key_lineage -> swing_active_arm_preopen_missing
- #5 `active_arm_09ab33ed46201071`: key_lineage -> swing_active_arm_preopen_missing
- #6 `active_arm_09fb0c4e52118008`: key_lineage -> swing_active_arm_preopen_missing
- #7 `active_arm_0e6d07fa10a5b582`: key_lineage -> swing_active_arm_preopen_missing
- #8 `active_arm_0fcffe09b9b7096c`: key_lineage -> swing_active_arm_preopen_missing
- #9 `active_arm_15f74aa27eef743d`: key_lineage -> swing_active_arm_preopen_missing
- #10 `active_arm_1661ca30f0d594fd`: key_lineage -> swing_active_arm_preopen_missing
- #11 `active_arm_19927b62a7101067`: key_lineage -> swing_active_arm_preopen_missing
- #12 `active_arm_1d0320c9c0014f17`: key_lineage -> swing_active_arm_preopen_missing
- #13 `active_arm_23ad3a8f679f1a81`: key_lineage -> swing_active_arm_preopen_missing
- #14 `active_arm_245ff6f8165ffd11`: key_lineage -> swing_active_arm_preopen_missing
- #15 `active_arm_257abeb83cf00bf9`: key_lineage -> swing_active_arm_preopen_missing
- #16 `active_arm_292c648e73675368`: key_lineage -> swing_active_arm_preopen_missing
- #17 `active_arm_2a12a8c2289c2d03`: key_lineage -> swing_active_arm_preopen_missing
- #18 `active_arm_2c44a9b1dd392eb3`: key_lineage -> swing_active_arm_preopen_missing
- #19 `active_arm_2d256010e69684c1`: key_lineage -> swing_active_arm_preopen_missing
- #20 `active_arm_2db2ffa0b0aedc2a`: key_lineage -> swing_active_arm_preopen_missing

## Real Conversion Queue
- none
