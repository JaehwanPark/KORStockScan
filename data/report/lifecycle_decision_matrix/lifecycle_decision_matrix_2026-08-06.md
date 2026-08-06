# Lifecycle Decision Matrix - 2026-08-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-06`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1364`
- source_rows_total: `1438`
- retained_rows: `1364`
- dropped_rows_by_source: `{'dedupe': 74}`
- joined_rows: `289`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `12` / `0`
- exit_bucket_count/workorders: `25` / `1`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `33`
- lifecycle_flow_complete_count: `2`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `2` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0034`
- incomplete_flow_reason_counts: `{'missing_submit': 532, 'missing_holding': 586, 'missing_exit': 544, 'missing_entry': 322, 'candidate_id_only': 333, 'scale_in_noise_only': 279, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 43}`
- bucket_directed_sim_probe: `{'observed_row_count': 103, 'matched_row_count': 0, 'background_row_count': 103, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 20, 'not_instrumented': 81, 'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 978 | 2 | -0.2059 | 0.0004 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 57 | 2 | -0.2059 | 0.007 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 3 | 2 | -0.8628 | 0.1333 | `hold_sample` | `EXIT` | False |
| `scale_in` | 279 | 278 | -0.6602 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 47 | 5 | -0.6576 | 0.0532 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 589, 'complete_flow_count': 2, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 2, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 3, 'direct_sim_record_incomplete_flow_count': 3, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 3, 'missing_submit': 3, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 1, 'missing_holding': 2, 'missing_exit': 2, 'scale_in_noise_only': 2}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 587, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1364, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0034, 'complete_flow_conversion_denominator': 45, 'complete_flow_conversion_rate': 0.0444, 'active_priority_incomplete_seed_count': 265, 'scale_in_followup_event_count': 279, 'scale_in_unique_flow_count': 201, 'scale_in_noise_flow_count': 279, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 279, 'active_priority_incomplete_seed_excluded': 265}, 'conversion_blocker_reason_counts': {'missing_entry': 43, 'missing_submit': 43, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 43, 'missing_holding': 42, 'candidate_id_only': 42}, 'observation_seed_reason_counts': {'missing_submit': 489, 'missing_holding': 544, 'missing_exit': 544, 'missing_entry': 279, 'candidate_id_only': 291, 'scale_in_noise_only': 279, 'sim_record_id_only': 2}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 978, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 964, 'candidate_id': 14}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 57, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 57}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 3, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 2, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 279, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 277, 'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 47, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 4, 'exact_sim_record_id': 1, 'candidate_id': 42}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 978, 'submit': 57, 'holding': 3, 'exit': 47}, 'incomplete_flow_reason_counts': {'missing_submit': 532, 'missing_holding': 586, 'missing_exit': 544, 'missing_entry': 322, 'candidate_id_only': 333, 'scale_in_noise_only': 279, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 43}, 'bucket_count': 33, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1729d68718` | 1 | 1 | -0.7 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 1 | 1 | -0.69 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 258 | 257 | -0.7434 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 21 | 21 | 0.3577 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 13 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:0370c0d68d` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 8 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:9eb64b35a4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 14 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:181ae7de9f` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b` | 79 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:337d794c66` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 978, 'bucket_count': 181, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 16, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 58 | 2 | -0.2059 | -1.515 | 0.5 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 14 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 30 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 619 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 12 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 244 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 13 | 1 | -0.686 | -3.18 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 8 | 1 | 0.2743 | 0.15 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `SKIP_PRE_SUBMIT_SAFETY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 57, 'bucket_count': 70, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 109, 'refresh_applied_count': 41, 'still_latency_blocked_after_refresh_count': 102, 'latency_pass_recovered_count': 7, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 4, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 487, 'ws_snapshot_refresh_failed_stale': 54}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 4, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 487, 'ws_snapshot_refresh_failed_stale': 54}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 1, 'price_guard_or_revalidation': 6}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 34, 'refresh_failed_quote_stale': 10, 'refresh_not_attempted_or_not_instrumented': 1, 'refresh_resolved_quote_freshness': 10, 'sim_submit_path_not_applicable': 2}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 44, 'refresh_not_attempted_or_not_instrumented': 1, 'sim_submit_path_not_applicable': 2, 'ws_snapshot_refresh_applied': 10}, 'real_submitted_row_count': 0, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 57 | 2 | -0.2059 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 57 | 2 | -0.2059 | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 34 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | 0.2743 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.686 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 18 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 18 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 9 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2 | 2 | -0.2059 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `quote_stale,ws_age_too_high,spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 54 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 2 | 2 | -0.2059 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 55 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 1 | -0.686 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1 | 1 | 0.2743 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 55 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 1 | 1 | -0.686 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1 | 1 | 0.2743 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 55 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 2 | 2 | -0.2059 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 55 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 2 | 2 | -0.2059 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 35 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 6 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_3_10s` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 2 | 2 | -0.2059 | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 44 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 10 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 2 | 2 | -0.2059 | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 54 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 2 | 2 | -0.2059 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_not_attempted_or_not_instrumented` | 1 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 3, 'source_row_count': 3, 'bucket_count': 12, 'joined_sample': 10, 'source_quality_adjusted_ev_pct': -0.8628, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.933 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2074 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 2 | 2 | -0.8628 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 2 | 2 | -0.8628 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2 | 2 | -0.8628 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -1.933 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.2074 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 47, 'source_row_count': 47, 'bucket_count': 25, 'joined_sample': 25, 'source_quality_adjusted_ev_pct': -0.6576, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 2 | 2 | -0.695 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.933 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.2074 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 37 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 5 | 0 | None | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 2 | 2 | -0.8628 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2 | 2 | -0.695 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 42 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2 | 2 | -0.695 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -1.933 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | 0.2074 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 37 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 5 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2 | 2 | -0.695 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2 | 2 | -0.8628 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 37 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 3 | -0.5208 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -1.933 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.2074 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 42 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `profit_band` / `profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 279, 'bucket_count': 67, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 258, 'PYRAMID': 21}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 270 | 270 | None | -0.7943 | 0.0481 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 8 | 8 | None | 0.48 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 118 | 118 | None | -0.7771 | 0.0339 | `hold_sample` |
| `ai_score_source` | `live` | 82 | 82 | None | -0.4566 | 0.2073 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 37 | 37 | None | -1.0019 | 0.0 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 23 | 23 | None | -1.483 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 16 | 16 | None | -0.5687 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 2 | 2 | None | -0.6 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 1 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 258 | 257 | None | -0.8457 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 21 | 21 | None | 0.32 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 256 | 255 | None | -0.8281 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 21 | 21 | None | 0.32 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2 | 2 | None | -3.09 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.61)` | 42 | 42 | None | -0.61 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.70)` | 36 | 36 | None | -0.7 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 26 | 26 | None | -0.99 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 24 | 24 | None | -0.89 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 23 | 23 | None | -0.23 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 2, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `holding` | 1 | 0 | None | None | None | `hold_sample` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- none

## Fixed Threshold Roles

- `hard_safety`: broker_submit_guard, stale_quote_submit_block, price_freshness_guard, hard_stop, protect_stop, emergency_stop, account_order_cooldown_qty_guard
- `baseline_prior`: BUY_SCORE_THRESHOLD, VPW_MIN_SCORE, strength_momentum_cutoff, entry_score_cutoff
- `bounded_tunable`: SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION, SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION, SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION, score65_74_recovery_probe, soft_stop_whipsaw_confirmation, holding_flow_override, scale_in_price_guard
- `legacy_archive`: fallback_scout_main, fallback_single, latency_fallback_split_entry, legacy_latency_composite, closed_shadow_axes

## Forbidden Uses

- `hard_safety_override`
- `real_execution_quality_from_sim_only`
- `intraday_threshold_mutation`
- `runtime_feature_future_label_leakage`
