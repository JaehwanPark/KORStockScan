# Key Lineage Ledger - 2026-06-15

## Decision
- source keys: `372`
- runtime observation target date: `2026-06-15`
- runtime policy source date: `2026-06-12`
- postclose candidate source date: `2026-06-15`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `3`
- positive EV runtime observed: `2`
- positive EV sample-floor blocked known floor: `10`
- positive EV sample-floor unknown floor: `5`
- positive EV sample-floor related total: `15`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`14399` zero_count=`8165` positive_count=`6234` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`9` counts=`{'canonical': 70, 'new_axis_pending_taxonomy': 9, 'unknown': 17}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 261163, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`10678` eligible=`1509` not_match_eligible=`9169` not_match_eligible_reasons=`{'diagnostic_followup_without_seed_context': 9169}` new_entry=`204` followup=`10474` matched=`9` matched_true_without_seed_id=`0` unmatched=`1500` new_entry_unmatched=`203` followup_unmatched=`1297` eligible_without_seed_id=`1500` raw_without_seed_id=`10669` eligible_followup_without_seed_id=`1297` raw_followup_without_seed_id=`10466`
- panic scale-in no-match: events=`4421` unique_sim_records=`81` missing_sim_record_id=`0` repeated_followup=`4340` status_counts=`{'policy_disabled': 6560, 'no_match': 4421, 'matched': 1115}` source_stage_counts=`{'blocked_ai_score': 3282, 'scale_in': 1138, 'first_ai_wait': 1}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`85`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_08846c77940cfa3e` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_102cfe8a5ee6ec9b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_117652d76d63ff34` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_120deebc97eec625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_136f942c5ddd1131` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c230a4bff6aa0e4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c60438d887840e3` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1fc6245cf630af1c` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_29e16cdf6d905126` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_2f3fd16a925e02c7` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_31323d9e3795b722` (active_seed): preopen_missing -> key_lineage_preopen_missing
