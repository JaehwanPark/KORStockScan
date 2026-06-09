# Key Lineage Ledger - 2026-06-09

## Decision
- source keys: `363`
- runtime observation target date: `2026-06-09`
- runtime policy source date: `2026-06-08`
- postclose candidate source date: `2026-06-09`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `6`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `22`
- positive EV sample-floor unknown floor: `4`
- positive EV sample-floor related total: `26`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`17427` zero_count=`0` positive_count=`17427` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`3` counts=`{'canonical': 24, 'new_axis_pending_taxonomy': 3, 'unknown': 23}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 274293, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`8315` new_entry=`180` followup=`8135` matched=`1848` matched_true_without_seed_id=`0` unmatched=`6467` new_entry_unmatched=`107` followup_unmatched=`6360` without_seed_id=`6467` followup_without_seed_id=`6360`
- panic scale-in no-match: events=`14850` unique_sim_records=`245` missing_sim_record_id=`0` repeated_followup=`14605` status_counts=`{'no_match': 14850}` source_stage_counts=`{'first_ai_wait': 1163, 'blocked_ai_score': 5553, 'scale_in': 8134}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`39`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_31323d9e3795b722` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_46465cc508b01988` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_4b18475c5eb7d75f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_4c1a53325fc1b0b2` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_4ea10f5a049bd932` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_66c7631520401b4b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_6eef2ac7c4ea05fa` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_71c8383ab022b485` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_760c98186c8de610` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_87556f8f4cca85ca` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_a8345805b646b14d` (active_seed): preopen_missing -> key_lineage_preopen_missing
