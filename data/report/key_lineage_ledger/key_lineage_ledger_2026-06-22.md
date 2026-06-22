# Key Lineage Ledger - 2026-06-22

## Decision
- source keys: `325`
- runtime observation target date: `2026-06-22`
- runtime policy source date: `2026-06-19`
- postclose candidate source date: `2026-06-22`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `9`
- positive EV runtime observed: `2`
- positive EV sample-floor blocked known floor: `12`
- positive EV sample-floor unknown floor: `2`
- positive EV sample-floor related total: `14`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`2468` zero_count=`0` positive_count=`2468` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`11` counts=`{'canonical': 76, 'new_axis_pending_taxonomy': 11, 'unknown': 17}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 82700, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`1941` eligible=`1941` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`153` followup=`1788` matched=`1852` matched_true_without_seed_id=`0` unmatched=`89` new_entry_unmatched=`5` followup_unmatched=`84` eligible_without_seed_id=`89` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 84, 'taxonomy_pending_or_natural_no_match': 5}` missing_parent_stages=`{'scalp_sim_pre_submit_liquidity_guard_would_block': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 5, 'scalp_sim_entry_submit_revalidation_warning': 5, 'scalp_sim_buy_order_virtual_pending': 5, 'scalp_sim_buy_order_assumed_filled': 5, 'scalp_sim_holding_started': 5, 'scalp_sim_sell_order_assumed_filled': 2, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 4, 'scalp_sim_panic_level1_entry_observed': 2, 'scalp_sim_panic_scale_in_blocked': 50}` raw_without_seed_id=`89` eligible_followup_without_seed_id=`84` raw_followup_without_seed_id=`84`
- panic scale-in no-match: events=`823` unique_sim_records=`134` missing_sim_record_id=`0` repeated_followup=`689` status_counts=`{'no_match': 823, 'matched': 48}` source_stage_counts=`{'first_ai_wait': 629, 'scale_in': 163, 'blocked_ai_score': 31}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`92`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_102cfe8a5ee6ec9b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_117652d76d63ff34` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_15409408ea5eaf12` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c218cd27c6c1e78` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c230a4bff6aa0e4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c60438d887840e3` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1fc6245cf630af1c` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_2475654ee0d096b1` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_29e16cdf6d905126` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_2f3fd16a925e02c7` (active_seed): preopen_missing -> key_lineage_preopen_missing
