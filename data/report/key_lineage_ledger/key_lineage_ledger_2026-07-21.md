# Key Lineage Ledger - 2026-07-21

## Decision
- source keys: `320`
- runtime observation target date: `2026-07-21`
- runtime policy source date: `2026-07-20`
- postclose candidate source date: `2026-07-21`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `1`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`72` zero_count=`0` positive_count=`72` id_without_count=`0` loaded_for_effect=`True` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`41` counts=`{'canonical': 113, 'new_axis_pending_taxonomy': 41, 'unknown': 13}`
- event IO guard: `{'mode': 'streaming_jsonl', 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 94067, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`68` eligible=`68` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`1` followup=`67` matched=`0` matched_true_without_seed_id=`0` unmatched=`68` new_entry_unmatched=`1` followup_unmatched=`67` eligible_without_seed_id=`68` without_seed_details=`{'parent_seed_id_not_propagated_to_followup': 67, 'taxonomy_pending_or_natural_no_match': 1}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{'scalp_sim_panic_level1_entry_observed': 1, 'scalp_sim_entry_ai_price_applied': 1, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 1, 'scalp_sim_buy_order_virtual_pending': 1, 'scalp_sim_buy_order_assumed_filled': 1, 'scalp_sim_holding_started': 1, 'scalp_sim_panic_scale_in_blocked': 60}` raw_without_seed_id=`68` eligible_followup_without_seed_id=`67` raw_followup_without_seed_id=`67`
- panic scale-in no-match: events=`64` unique_sim_records=`2` missing_sim_record_id=`0` repeated_followup=`62` status_counts=`{'no_match': 64}` source_stage_counts=`{'blocked_ai_score': 60, 'scale_in': 4}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`210`, not_instrumented=`0`

## Top Blockers
- `active_seed_036294d34ba9e40f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0629ba2d0f4dd524` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_06fce89fd3a136e6` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_070283a402558852` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0747f150d4c2eab8` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_07677c2e78c144df` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_076f28062ca5e731` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0a9736d86332c717` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0be328a60ec0d5f5` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0beafbebc75f56c4` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0cae3a2115d07d28` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_0f89d368fef8e904` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_10149f9668d463a9` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_102cfe8a5ee6ec9b` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1051123340ab344f` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1096e7d8ada1ee8a` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_109a6ab7807c9624` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_117652d76d63ff34` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_120deebc97eec625` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_1307cd5fa2e96df9` (active_seed): preopen_missing -> key_lineage_preopen_missing
