# Key Lineage Ledger - 2026-06-17

## Decision
- source keys: `323`
- runtime observation target date: `2026-06-17`
- runtime policy source date: `2026-06-16`
- postclose candidate source date: `2026-06-17`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `8`
- positive EV runtime observed: `6`
- positive EV sample-floor blocked known floor: `24`
- positive EV sample-floor unknown floor: `4`
- positive EV sample-floor related total: `28`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`1628` zero_count=`0` positive_count=`1628` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`9` counts=`{'canonical': 73, 'new_axis_pending_taxonomy': 9, 'unknown': 17}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 494127, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`1010` eligible=`1010` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`117` followup=`893` matched=`380` matched_true_without_seed_id=`0` unmatched=`630` new_entry_unmatched=`74` followup_unmatched=`556` eligible_without_seed_id=`630` raw_without_seed_id=`630` eligible_followup_without_seed_id=`556` raw_followup_without_seed_id=`556`
- panic scale-in no-match: events=`136` unique_sim_records=`20` missing_sim_record_id=`0` repeated_followup=`116` status_counts=`{'no_match': 136, 'matched': 9}` source_stage_counts=`{'scale_in': 53, 'first_ai_wait': 30, 'blocked_ai_score': 53}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`87`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_102cfe8a5ee6ec9b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_117652d76d63ff34` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_120deebc97eec625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c230a4bff6aa0e4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c60438d887840e3` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1fc6245cf630af1c` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_2f3fd16a925e02c7` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_31323d9e3795b722` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_33407b49d7994226` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_3a7518afb6293b0f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_3b93efada5dda062` (active_seed): preopen_missing -> key_lineage_preopen_missing
