# Key Lineage Ledger - 2026-07-10

## Decision
- source keys: `318`
- runtime observation target date: `2026-07-10`
- runtime policy source date: `2026-07-09`
- postclose candidate source date: `2026-07-10`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `4`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `3`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `3`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`271` zero_count=`271` positive_count=`0` id_without_count=`0` loaded_for_effect=`False` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`27` counts=`{'canonical': 97, 'new_axis_pending_taxonomy': 27, 'unknown': 16}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 72435, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`271` eligible=`271` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`38` followup=`233` matched=`8` matched_true_without_seed_id=`0` unmatched=`263` new_entry_unmatched=`37` followup_unmatched=`226` eligible_without_seed_id=`263` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 226, 'taxonomy_pending_or_natural_no_match': 37}` inferred_parent_seed_id=`8` inferred_stages=`{'scalp_sim_entry_ai_price_applied': 1, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 1, 'scalp_sim_entry_armed': 1, 'scalp_sim_buy_order_virtual_pending': 1, 'scalp_sim_buy_order_assumed_filled': 1, 'scalp_sim_holding_started': 1, 'scalp_sim_scale_in_order_unfilled': 1}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_entry_ai_price_applied': 34, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 25, 'scalp_sim_pre_submit_overbought_guard_would_pass': 37, 'scalp_sim_buy_order_virtual_pending': 37, 'scalp_sim_buy_order_assumed_filled': 37, 'scalp_sim_holding_started': 37, 'scalp_sim_sell_order_assumed_filled': 7, 'scalp_sim_pre_submit_liquidity_guard_would_block': 12}` raw_without_seed_id=`271` eligible_followup_without_seed_id=`226` raw_followup_without_seed_id=`233`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{}` source_stage_counts=`{}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`158`, not_instrumented=`0`

## Top Blockers
- `active_seed_03c539e6527cdda2` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_076f28062ca5e731` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_08846c77940cfa3e` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0be328a60ec0d5f5` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0beafbebc75f56c4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0f89d368fef8e904` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_102cfe8a5ee6ec9b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1051123340ab344f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_117652d76d63ff34` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_120deebc97eec625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_136f942c5ddd1131` (active_seed): preopen_missing -> key_lineage_preopen_missing
