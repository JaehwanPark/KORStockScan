# Key Lineage Ledger - 2026-06-24

## Decision
- source keys: `284`
- runtime observation target date: `2026-06-24`
- runtime policy source date: `2026-06-23`
- postclose candidate source date: `2026-06-24`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `8`
- positive EV runtime observed: `1`
- positive EV sample-floor blocked known floor: `4`
- positive EV sample-floor unknown floor: `5`
- positive EV sample-floor related total: `9`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`2701` zero_count=`0` positive_count=`2701` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`14` counts=`{'canonical': 78, 'new_axis_pending_taxonomy': 14, 'unknown': 17}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 184175, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`2598` eligible=`2598` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`118` followup=`2480` matched=`1948` matched_true_without_seed_id=`0` unmatched=`650` new_entry_unmatched=`28` followup_unmatched=`622` eligible_without_seed_id=`650` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 622, 'taxonomy_pending_or_natural_no_match': 28}` missing_parent_stages=`{'scalp_sim_pre_submit_liquidity_guard_would_pass': 16, 'scalp_sim_pre_submit_overbought_guard_would_pass': 28, 'scalp_sim_entry_submit_revalidation_warning': 27, 'scalp_sim_buy_order_virtual_pending': 28, 'scalp_sim_buy_order_assumed_filled': 28, 'scalp_sim_holding_started': 28, 'scalp_sim_sell_order_assumed_filled': 19, 'scalp_sim_panic_level1_entry_observed': 22, 'scalp_sim_pre_submit_liquidity_guard_would_block': 12, 'scalp_sim_panic_scale_in_blocked': 410, 'scalp_sim_panic_bottoming_entry_allowed': 4}` raw_without_seed_id=`650` eligible_followup_without_seed_id=`622` raw_followup_without_seed_id=`622`
- panic scale-in no-match: events=`1609` unique_sim_records=`91` missing_sim_record_id=`0` repeated_followup=`1518` status_counts=`{'no_match': 1609, 'matched': 57}` source_stage_counts=`{'first_ai_wait': 1135, 'blocked_ai_score': 422, 'scale_in': 52}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`132`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
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
- `active_seed_15409408ea5eaf12` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c218cd27c6c1e78` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c230a4bff6aa0e4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c60438d887840e3` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1fc6245cf630af1c` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_2f3fd16a925e02c7` (active_seed): preopen_missing -> key_lineage_preopen_missing
