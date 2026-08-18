# Key Lineage Ledger - 2026-08-18

## Decision
- source keys: `75`
- runtime observation target date: `2026-08-18`
- runtime policy source date: `2026-08-14`
- postclose candidate source date: `2026-08-18`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `0`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `1`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`927` zero_count=`927` positive_count=`0` id_without_count=`0` loaded_for_effect=`False` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`5` counts=`{'canonical': 27, 'new_axis_pending_taxonomy': 5}`
- event IO guard: `{'mode': 'streaming_jsonl', 'gzip_supported': True, 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 330669, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`920` eligible=`0` not_match_eligible=`920` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 920}` new_entry=`25` followup=`895` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`920` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`895`
- panic scale-in no-match: events=`692` unique_sim_records=`13` missing_sim_record_id=`0` repeated_followup=`679` status_counts=`{'no_match': 692}` source_stage_counts=`{'blocked_ai_score': 692}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`0`, not_instrumented=`0`

## Top Blockers
- none
