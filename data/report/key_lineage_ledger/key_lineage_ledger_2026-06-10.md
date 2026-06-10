# Key Lineage Ledger - 2026-06-10

## Decision
- source keys: `365`
- runtime observation target date: `2026-06-10`
- runtime policy source date: `2026-06-09`
- postclose candidate source date: `2026-06-10`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `0`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `12`
- positive EV sample-floor unknown floor: `6`
- positive EV sample-floor related total: `18`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`17585` zero_count=`17585` positive_count=`0` id_without_count=`0` loaded_for_effect=`False` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`5` counts=`{'canonical': 53, 'new_axis_pending_taxonomy': 5, 'unknown': 19}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 325931, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`1276` new_entry=`79` followup=`1197` matched=`0` matched_true_without_seed_id=`0` unmatched=`1276` new_entry_unmatched=`79` followup_unmatched=`1197` without_seed_id=`1276` followup_without_seed_id=`1197`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_disabled': 13434}` source_stage_counts=`{}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`47`, not_instrumented=`0`

## Top Blockers
- `active_seed_03c539e6527cdda2` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_136f942c5ddd1131` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_31323d9e3795b722` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_44e1edd653df5f36` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_46465cc508b01988` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_4b18475c5eb7d75f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_4c1a53325fc1b0b2` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_4ea10f5a049bd932` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_5de7caf844ddc438` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_5fbf3e3baf24631e` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_66c7631520401b4b` (active_seed): preopen_missing -> key_lineage_preopen_missing
