# Key Lineage Ledger - 2026-07-06

## Decision
- source keys: `302`
- runtime observation target date: `2026-07-06`
- runtime policy source date: `2026-07-03`
- postclose candidate source date: `2026-07-06`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `7`
- positive EV runtime observed: `1`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `1`
- positive EV sample-floor related total: `4`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`955` zero_count=`0` positive_count=`955` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`19` counts=`{'canonical': 95, 'new_axis_pending_taxonomy': 19, 'unknown': 16}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 93645, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`882` eligible=`882` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`67` followup=`815` matched=`546` matched_true_without_seed_id=`0` unmatched=`336` new_entry_unmatched=`21` followup_unmatched=`315` eligible_without_seed_id=`336` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 315, 'taxonomy_pending_or_natural_no_match': 21}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_pre_submit_liquidity_guard_would_block': 11, 'scalp_sim_pre_submit_overbought_guard_would_pass': 21, 'scalp_sim_buy_order_virtual_pending': 21, 'scalp_sim_buy_order_assumed_filled': 21, 'scalp_sim_holding_started': 21, 'scalp_sim_sell_order_assumed_filled': 4, 'scalp_sim_entry_ai_price_applied': 19, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 10, 'scalp_sim_panic_level1_entry_observed': 15, 'scalp_sim_panic_scale_in_blocked': 167, 'scalp_sim_scale_in_order_unfilled': 4, 'scalp_sim_scale_in_order_assumed_filled': 1}` raw_without_seed_id=`336` eligible_followup_without_seed_id=`315` raw_followup_without_seed_id=`315`
- panic scale-in no-match: events=`347` unique_sim_records=`32` missing_sim_record_id=`0` repeated_followup=`315` status_counts=`{'no_match': 347, 'matched': 23}` source_stage_counts=`{'first_ai_wait': 175, 'blocked_ai_score': 172}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`136`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_076f28062ca5e731` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_08846c77940cfa3e` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0be328a60ec0d5f5` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0f89d368fef8e904` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_102cfe8a5ee6ec9b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1051123340ab344f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_120deebc97eec625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c218cd27c6c1e78` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c230a4bff6aa0e4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_24a139dfb60cb311` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_29e16cdf6d905126` (active_seed): preopen_missing -> key_lineage_preopen_missing
