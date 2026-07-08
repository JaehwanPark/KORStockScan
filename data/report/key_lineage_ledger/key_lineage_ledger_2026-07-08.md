# Key Lineage Ledger - 2026-07-08

## Decision
- source keys: `314`
- runtime observation target date: `2026-07-08`
- runtime policy source date: `2026-07-07`
- postclose candidate source date: `2026-07-08`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `4`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `2`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `2`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`1428` zero_count=`1428` positive_count=`0` id_without_count=`0` loaded_for_effect=`False` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`23` counts=`{'canonical': 96, 'new_axis_pending_taxonomy': 23, 'unknown': 16}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 105913, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`1420` eligible=`1420` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`73` followup=`1347` matched=`1037` matched_true_without_seed_id=`0` unmatched=`383` new_entry_unmatched=`29` followup_unmatched=`354` eligible_without_seed_id=`383` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 354, 'taxonomy_pending_or_natural_no_match': 29}` inferred_parent_seed_id=`1037` inferred_stages=`{'scalp_sim_entry_ai_price_applied': 44, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 24, 'scalp_sim_pre_submit_overbought_guard_would_pass': 43, 'scalp_sim_entry_armed': 44, 'scalp_sim_buy_order_virtual_pending': 44, 'scalp_sim_buy_order_assumed_filled': 44, 'scalp_sim_holding_started': 44, 'scalp_sim_pre_submit_liquidity_guard_would_block': 20, 'scalp_sim_scale_in_order_unfilled': 2, 'scalp_sim_sell_order_assumed_filled': 19, 'scalp_sim_panic_level1_entry_observed': 22, 'scalp_sim_panic_scale_in_blocked': 685, 'scalp_sim_panic_bottoming_entry_allowed': 1, 'scalp_sim_pre_submit_overbought_guard_would_block': 1}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_entry_ai_price_applied': 27, 'scalp_sim_pre_submit_liquidity_guard_would_block': 11, 'scalp_sim_pre_submit_overbought_guard_would_pass': 28, 'scalp_sim_buy_order_virtual_pending': 29, 'scalp_sim_buy_order_assumed_filled': 29, 'scalp_sim_holding_started': 29, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 18, 'scalp_sim_panic_scale_in_blocked': 157, 'scalp_sim_panic_level1_entry_observed': 12, 'scalp_sim_sell_order_assumed_filled': 7, 'scalp_sim_pre_submit_overbought_guard_would_block': 1, 'scalp_sim_scale_in_order_unfilled': 5, 'scalp_sim_scale_in_order_assumed_filled': 1}` raw_without_seed_id=`1420` eligible_followup_without_seed_id=`354` raw_followup_without_seed_id=`1347`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 842}` source_stage_counts=`{}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`144`, not_instrumented=`0`

## Top Blockers
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
- `active_seed_120deebc97eec625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c218cd27c6c1e78` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c230a4bff6aa0e4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1c60438d887840e3` (active_seed): preopen_missing -> key_lineage_preopen_missing
