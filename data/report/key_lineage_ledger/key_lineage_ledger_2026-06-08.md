# Key Lineage Ledger - 2026-06-08

## Decision
- source keys: `351`
- runtime observation target date: `2026-06-08`
- runtime policy source date: `2026-06-05`
- postclose candidate source date: `2026-06-08`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `9`
- positive EV runtime observed: `4`
- positive EV sample-floor blocked known floor: `23`
- positive EV sample-floor unknown floor: `1`
- positive EV sample-floor related total: `24`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`20078` zero_count=`10829` positive_count=`9249` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`0` counts=`{'unknown': 31}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 303744, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`4043` new_entry=`74` followup=`3969` matched=`44` matched_true_without_seed_id=`0` unmatched=`3999` new_entry_unmatched=`72` followup_unmatched=`3927` without_seed_id=`3999` followup_without_seed_id=`3927`
- panic scale-in no-match: events=`5506` unique_sim_records=`121` missing_sim_record_id=`0` repeated_followup=`5385` status_counts=`{'no_match': 5506, 'matched': 11089}` source_stage_counts=`{'first_ai_wait': 2343, 'blocked_ai_score': 898, 'scale_in': 2265}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`23`, not_instrumented=`0`

## Top Blockers
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_46465cc508b01988` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_760c98186c8de610` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_7cf1c198fc1e5246` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_afa0c4f1bdf63001` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_bef67812d7545625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_c332627f82811a7c` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_dca8f64a0b44d10b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_e7edaab436e6cafc` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_ffbb1f0655af37f0` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_arm_0c383886ae3c8de3` (active_arm): preopen_missing -> swing_active_arm_preopen_missing
- `active_arm_342af4565cfdbf29` (active_arm): preopen_missing -> swing_active_arm_preopen_missing
- `active_arm_790e3894639690bd` (active_arm): preopen_missing -> swing_active_arm_preopen_missing
- `active_arm_7bc3260124b31b77` (active_arm): preopen_missing -> swing_active_arm_preopen_missing
- `active_arm_83b3cc10ef194674` (active_arm): preopen_missing -> swing_active_arm_preopen_missing
