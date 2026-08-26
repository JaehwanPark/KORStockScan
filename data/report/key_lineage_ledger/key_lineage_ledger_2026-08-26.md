# Key Lineage Ledger - 2026-08-26

## Decision
- source keys: `66`
- runtime observation target date: `2026-08-26`
- runtime policy source date: `2026-08-25`
- postclose candidate source date: `2026-08-26`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `1`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `3`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`143` zero_count=`0` positive_count=`143` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`4` counts=`{'canonical': 27, 'new_axis_pending_taxonomy': 4}`
- event IO guard: `{'mode': 'streaming_jsonl', 'gzip_supported': True, 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 264379, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`143` eligible=`143` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`17` followup=`126` matched=`16` matched_true_without_seed_id=`0` unmatched=`127` new_entry_unmatched=`15` followup_unmatched=`112` eligible_without_seed_id=`0` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`127` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`112`
- panic scale-in no-match: events=`5` unique_sim_records=`2` missing_sim_record_id=`0` repeated_followup=`3` status_counts=`{'no_match': 5}` source_stage_counts=`{'blocked_ai_score': 5}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`0`, not_instrumented=`0`

## Top Blockers
- none
