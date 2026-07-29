# Lifecycle Decision Matrix - 2026-07-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-28`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `83`
- source_rows_total: `242`
- retained_rows: `83`
- dropped_rows_by_source: `{'dedupe': 159}`
- joined_rows: `6`
- policy_pass_count: `0`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `5` / `0`
- exit_bucket_count/workorders: `5` / `0`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `13`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `0` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_holding': 38, 'missing_exit': 38, 'missing_entry': 8, 'missing_submit': 14, 'candidate_id_only': 5, 'scale_in_noise_only': 5, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}`
- bucket_directed_sim_probe: `{'observed_row_count': 2, 'matched_row_count': 0, 'background_row_count': 2, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `['all_stage_policy_entries_below_sample_floor']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 51 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 25 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 1 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 5 | 5 | -0.7692 | 0.5 | `hold_sample` | `NO_CHANGE` | False |
| `exit` | 1 | 1 | -0.1725 | 0.1 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 39, 'complete_flow_count': 0, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 0, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'producer_missing_sim_record_on_required_stage', 'direct_flow_zero_closure_status': 'producer_followup_required', 'direct_flow_zero_followup_required': True, 'direct_sim_record_flow_count': 1, 'direct_sim_record_incomplete_flow_count': 1, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 1, 'missing_submit': 1, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'producer_missing_sim_record_on_required_stage', 'direct_flow_zero_closure_status': 'producer_followup_required', 'direct_flow_zero_followup_required': True, 'incomplete_flow_count': 39, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 83, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'complete_flow_conversion_denominator': 3, 'complete_flow_conversion_rate': 0.0, 'active_priority_incomplete_seed_count': 31, 'scale_in_followup_event_count': 5, 'scale_in_unique_flow_count': 5, 'scale_in_noise_flow_count': 5, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 5, 'active_priority_incomplete_seed_excluded': 31}, 'conversion_blocker_reason_counts': {'missing_entry': 3, 'missing_holding': 2, 'missing_exit': 2, 'missing_submit': 1, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}, 'observation_seed_reason_counts': {'missing_holding': 36, 'missing_exit': 36, 'missing_submit': 13, 'missing_entry': 5, 'candidate_id_only': 5, 'scale_in_noise_only': 5}, 'join_contract_blocked': True, 'bundle_ev_tuning_state': 'blocked_join_gap', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 51, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 51}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 25, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 25}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 5, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 5}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 51, 'submit': 25, 'holding': 1, 'exit': 1}, 'incomplete_flow_reason_counts': {'missing_holding': 38, 'missing_exit': 38, 'missing_entry': 8, 'missing_submit': 14, 'candidate_id_only': 5, 'scale_in_noise_only': 5, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}, 'bucket_count': 13, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4 | 4 | -1.1165 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | 0.62 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8a9ce220d7` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:daa7e36576` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:43870ece59` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5fc5abcf3e` | 10 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee469a4fb` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b22dfc875d` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:67845aaedc` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 51, 'bucket_count': 37, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `BUY_DEFENSIVE` | 9 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 33 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 21 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 13 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 51 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 2 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 49 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_chase_risk` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 25, 'bucket_count': 45, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 9, 'refresh_applied_count': 9, 'still_latency_blocked_after_refresh_count': 0, 'latency_pass_recovered_count': 1, 'order_bundle_submitted_after_refresh_count': 1, 'refresh_subreason_counts': {}, 'refresh_block_subreason_counts': {}, 'latency_pass_recovered_downstream_counts': {'order_bundle_submitted': 1}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 12, 'refresh_resolved_quote_freshness': 13}, 'pre_submit_refresh_applied_counts': {'observer_quote_refresh_applied': 1, 'refresh_not_attempted_or_not_instrumented': 12, 'ws_snapshot_refresh_applied': 12}, 'real_submitted_row_count': 12, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 13 | 0 | None | `keep_collecting` |
| `actual_order_submitted` | `true` | 12 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 13 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 12 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 13 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 11 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 13 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 10 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 2 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 25 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 25 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `observer_quote_refresh_applied` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 13 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_not_attempted_or_not_instrumented` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `refresh_reason_not_instrumented` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `ws_snapshot:latest_ws_snapshot_fresh` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `observer_quote:observer_quote_fresh` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `refresh_source_not_instrumented` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `ws_manager_latest_data` | 12 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `orderbook_stability_observer` | 1 | 0 | None | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 25 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_not_available_pre_submit` | 13 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `resolved_price` | 12 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 13 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 11 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_lt1s` | 1 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_resolved_quote_freshness` | 13 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 1, 'source_row_count': 1, 'bucket_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1, 'source_row_count': 1, 'bucket_count': 5, 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -0.1725, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 5, 'bucket_count': 26, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 4, 'PYRAMID': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 5 | 5 | None | -0.908 | 0.2 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3 | 3 | None | -1.6433 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 2 | 2 | None | 0.195 | 0.5 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4 | 4 | None | -1.29 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 1 | 1 | None | 0.62 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4 | 4 | None | -1.29 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1 | 1 | None | 0.62 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 1 | 1 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.62)` | 1 | 1 | None | -0.62 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 1 | 1 | None | -0.88 | 0.0 | `hold_sample` |
| `blocker_reason` | `probe_expand_forbidden` | 1 | 1 | None | -3.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1 | 1 | None | 0.62 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 2 | None | -1.405 | 0.5 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 1 | None | -0.88 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 1 | None | -0.62 | 0.0 | `hold_sample` |
| `held_bucket` | `held_lt020s` | 1 | 1 | None | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3 | 3 | None | -0.5767 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 2 | None | -1.405 | 0.5 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 5 | 5 | None | -0.908 | 0.2 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | None | -2.155 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 2, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
