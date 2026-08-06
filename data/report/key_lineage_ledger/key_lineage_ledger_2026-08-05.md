# Key Lineage Ledger - 2026-08-05

## Decision
- source keys: `227`
- runtime observation target date: `2026-08-05`
- runtime policy source date: `2026-08-04`
- postclose candidate source date: `2026-08-05`
- new postclose candidate due state: `not_due_until_next_preopen`
- same-key continuity pass: `4`
- positive EV runtime observed: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`lineage_rows` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` basis=`lineage_evidence_sample_vs_sample_floor`
- active sim policy windows: events=`204` zero_count=`204` positive_count=`0` id_without_count=`0` loaded_for_effect=`False` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`47` counts=`{'canonical': 131, 'new_axis_pending_taxonomy': 47, 'unknown': 12}`
- event IO guard: `{'mode': 'streaming_jsonl', 'gzip_supported': True, 'untracked_value_limit_per_field': 200000, 'line_bytes_limit': 8000000, 'files_seen': 1, 'lines_read': 612745, 'json_decode_error_count': 0, 'file_read_error_count': 0, 'oversized_line_skipped_count': 0, 'truncated_untracked_value_count': 0, 'truncated_untracked_value_count_by_field': {}, 'truncated_panic_sim_record_id_count': 0, 'truncated_panic_no_match_sim_record_id_count': 0}`
- active seed candidate validation: total=`202` eligible=`0` not_match_eligible=`202` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 202}` new_entry=`4` followup=`198` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_details=`{}` inferred_parent_seed_id=`72` inferred_stages=`{'scalp_sim_panic_level1_entry_observed': 19, 'scalp_sim_entry_ai_price_skip_order': 26, 'scalp_sim_entry_ai_price_applied': 1, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 1, 'scalp_sim_entry_armed': 1, 'scalp_sim_buy_order_virtual_pending': 1, 'scalp_sim_buy_order_assumed_filled': 1, 'scalp_sim_holding_started': 1, 'scalp_sim_panic_scale_in_blocked': 18, 'scalp_sim_sell_order_assumed_filled': 1, 'scalp_sim_panic_bottoming_entry_allowed': 1}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`202` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`198`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 76}` source_stage_counts=`{}`
- blockers: mismatch=`0`, catalog_missing=`0`, preopen_missing=`3`, not_instrumented=`0`

## Top Blockers
- `active_seed_7cf1c198fc1e5246` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_94696687ea1be0c3` (active_seed): preopen_missing -> key_lineage_preopen_missing
- `active_seed_b99a2dea7aac2a83` (active_seed): preopen_missing -> key_lineage_preopen_missing
