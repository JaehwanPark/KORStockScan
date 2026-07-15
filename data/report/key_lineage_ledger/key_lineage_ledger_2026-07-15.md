# Key Lineage Ledger - 2026-07-15

## Decision
- source keys: `311`
- runtime observation target date: `2026-07-15`
- runtime policy source date: `2026-07-14`
- postclose candidate source date: `2026-07-15`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `3`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `1`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`841` zero_count=`0` positive_count=`841` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`37` counts=`{'canonical': 103, 'new_axis_pending_taxonomy': 37, 'unknown': 13}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 78493, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`835` eligible=`835` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`20` followup=`815` matched=`0` matched_true_without_seed_id=`0` unmatched=`835` new_entry_unmatched=`20` followup_unmatched=`815` eligible_without_seed_id=`835` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 815, 'taxonomy_pending_or_natural_no_match': 20}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_panic_level1_entry_observed': 18, 'scalp_sim_entry_ai_price_applied': 19, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 13, 'scalp_sim_pre_submit_overbought_guard_would_pass': 20, 'scalp_sim_buy_order_virtual_pending': 20, 'scalp_sim_buy_order_assumed_filled': 20, 'scalp_sim_holding_started': 20, 'scalp_sim_panic_scale_in_blocked': 674, 'scalp_sim_pre_submit_liquidity_guard_would_block': 7, 'scalp_sim_sell_order_assumed_filled': 4}` raw_without_seed_id=`835` eligible_followup_without_seed_id=`815` raw_followup_without_seed_id=`815`
- panic scale-in no-match: events=`674` unique_sim_records=`17` missing_sim_record_id=`0` repeated_followup=`657` status_counts=`{'no_match': 674}` source_stage_counts=`{'first_ai_wait': 513, 'blocked_ai_score': 161}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`167`, not_instrumented=`0`

## Top Blockers
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_076f28062ca5e731` (active_seed): preopen_missing -> key_lineage_preopen_missing
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
- `active_seed_1bf19f326d4bbdbd` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c218cd27c6c1e78` (active_seed): preopen_missing -> key_lineage_preopen_missing
