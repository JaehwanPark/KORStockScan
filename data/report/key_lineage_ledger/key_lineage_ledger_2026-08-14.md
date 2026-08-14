# Key Lineage Ledger - 2026-08-14

## Decision
- source keys: `66`
- runtime observation target date: `2026-08-14`
- runtime policy source date: `2026-08-13`
- postclose candidate source date: `2026-08-14`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `2`
- positive EV runtime observed: `1`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `1`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`226` zero_count=`0` positive_count=`226` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`3` counts=`{'canonical': 17, 'new_axis_pending_taxonomy': 3}`
- event IO guard: `{'mode': 'streaming_jsonl', 'gzip_supported': True, 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 311915, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`158` eligible=`158` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`15` followup=`143` matched=`139` matched_true_without_seed_id=`0` unmatched=`19` new_entry_unmatched=`2` followup_unmatched=`17` eligible_without_seed_id=`0` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`18` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`16`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'matched': 49}` source_stage_counts=`{}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`0`, not_instrumented=`0`

## Top Blockers
- none
