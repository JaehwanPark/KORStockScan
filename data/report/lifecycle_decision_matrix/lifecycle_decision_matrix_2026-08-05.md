# Lifecycle Decision Matrix - 2026-08-05

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-05`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `835`
- source_rows_total: `914`
- retained_rows: `835`
- dropped_rows_by_source: `{'dedupe': 79}`
- joined_rows: `100`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `7` / `5`
- exit_bucket_count/workorders: `27` / `5`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `25`
- lifecycle_flow_complete_count: `4`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `4` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0105`
- incomplete_flow_reason_counts: `{'missing_submit': 378, 'missing_holding': 378, 'missing_exit': 317, 'missing_entry': 141, 'candidate_id_only': 175, 'scale_in_noise_only': 80, 'postclose_exit_without_entry': 61, 'sim_record_id_only': 4}`
- bucket_directed_sim_probe: `{'observed_row_count': 166, 'matched_row_count': 0, 'background_row_count': 166, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 116, 'policy_missing': 50}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 678 | 4 | -0.7348 | 0.0024 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 4 | 4 | -0.7348 | 0.4 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 4 | 4 | -1.0151 | 0.4 | `hold_sample` | `EXIT` | False |
| `scale_in` | 80 | 80 | -1.0037 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 69 | 8 | -0.8713 | 0.0928 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 382, 'complete_flow_count': 4, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 4, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 4, 'direct_sim_record_incomplete_flow_count': 4, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 4, 'missing_submit': 4, 'missing_holding': 4, 'missing_exit': 4, 'sim_record_id_only': 4, 'scale_in_noise_only': 4}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 378, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 835, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0105, 'complete_flow_conversion_denominator': 65, 'complete_flow_conversion_rate': 0.0615, 'active_priority_incomplete_seed_count': 237, 'scale_in_followup_event_count': 80, 'scale_in_unique_flow_count': 61, 'scale_in_noise_flow_count': 80, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 80, 'active_priority_incomplete_seed_excluded': 237}, 'conversion_blocker_reason_counts': {'missing_entry': 61, 'missing_submit': 61, 'missing_holding': 61, 'candidate_id_only': 61, 'postclose_exit_without_entry': 61}, 'observation_seed_reason_counts': {'missing_submit': 317, 'missing_holding': 317, 'missing_exit': 317, 'missing_entry': 80, 'candidate_id_only': 114, 'scale_in_noise_only': 80, 'sim_record_id_only': 4}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 678, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 640, 'candidate_id': 38}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 4, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 4}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 4, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 80, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 76, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 69, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 8, 'candidate_id': 61}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 678, 'submit': 4, 'holding': 4, 'exit': 69}, 'incomplete_flow_reason_counts': {'missing_submit': 378, 'missing_holding': 378, 'missing_exit': 317, 'missing_entry': 141, 'candidate_id_only': 175, 'scale_in_noise_only': 80, 'postclose_exit_without_entry': 61, 'sim_record_id_only': 4}, 'bucket_count': 25, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 1 | 1 | -0.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 69 | 69 | -1.3014 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 11 | 11 | 0.8635 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f36cc32176` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:db8bbc6230` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 13 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 6 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1c4ab1bc7c` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 32 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 9 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:63006383a0` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b1a207eccf` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 41 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 678, 'bucket_count': 160, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 51 | 3 | -0.8496 | -2.12 | 0.0 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 578 | 1 | -0.3905 | 1.35 | 1.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 35 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 20 | 2 | -1.1674 | -2.475 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | -0.3905 | 1.35 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 10 | 1 | -0.2139 | -1.41 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_bottoming_entry_allowed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 4 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 4, 'bucket_count': 32, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': False, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 3, 'refresh_applied_count': 0, 'still_latency_blocked_after_refresh_count': 2, 'latency_pass_recovered_count': 0, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 2}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 2}, 'latency_pass_recovered_downstream_counts': {}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'sim_submit_path_not_applicable': 4}, 'pre_submit_refresh_applied_counts': {'sim_submit_path_not_applicable': 4}, 'real_submitted_row_count': 0, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4 | 4 | -0.7348 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4 | 4 | -0.7348 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -0.2139 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.6701 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | -0.3905 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -3.0049 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 4 | 4 | -0.7348 | `keep_collecting` |
| `latency_state` | `simulated` | 4 | 4 | -0.7348 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 3 | 3 | 0.0219 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 1 | -3.0049 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 3 | 3 | 0.0219 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1 | 1 | -3.0049 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 3 | 3 | -0.8496 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1 | 1 | -0.3905 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 4 | 4 | -0.7348 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 4 | 4 | -0.7348 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 4 | 4 | -0.7348 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 4 | 4 | -0.7348 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 4 | 4 | -0.7348 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 4 | 4 | -0.7348 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 4 | 4 | -0.7348 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 3 | 3 | 0.0219 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 1 | 1 | -3.0049 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 3 | 3 | 0.0219 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 1 | 1 | -3.0049 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 4 | 4 | -0.7348 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 4 | 4 | -0.7348 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 3 | 3 | 0.0219 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1 | 1 | -3.0049 | `keep_collecting` |
| `would_limit_fill` | `true` | 2 | 2 | 0.1398 | `keep_collecting` |
| `would_limit_fill` | `false` | 1 | 1 | -0.2139 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1 | 1 | -3.0049 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 4, 'source_row_count': 4, 'bucket_count': 7, 'joined_sample': 20, 'source_quality_adjusted_ev_pct': -1.0151, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -1.5055 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.4563 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 4 | 4 | -1.0151 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 4 | 4 | -1.0151 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 4 | 4 | -1.0151 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 3 | 3 | -1.5055 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 69, 'source_row_count': 69, 'bucket_count': 27, 'joined_sample': 40, 'source_quality_adjusted_ev_pct': -0.8713, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -0.885 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 2 | 2 | -0.57 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4053 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.8137 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -3.2975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 53 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 8 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 4 | 4 | -0.7275 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -1.4206 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 1 | 1 | -0.4053 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | -0.8137 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 61 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 4 | 4 | -0.7275 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.6095 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -3.2975 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | 0.4563 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 53 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 8 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 4 | 4 | -0.7275 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 4 | 4 | -1.0151 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 53 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 8 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 5 | 5 | -1.2573 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.57 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 61 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 80, 'bucket_count': 54, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 69, 'PYRAMID': 11}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 74 | 74 | None | -1.2974 | 0.0676 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 6 | 6 | None | 1.1767 | 1.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 33 | 33 | None | -0.8882 | 0.0303 | `hold_sample` |
| `ai_score_source` | `live` | 23 | 23 | None | -1.3348 | 0.4348 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 18 | 18 | None | -1.2278 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 4 | 4 | None | -0.6 | 0.0 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 2 | 2 | None | -2.22 | 0.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 69 | 69 | None | -1.4238 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 11 | 11 | None | 0.8445 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 69 | 69 | None | -1.4238 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 11 | 11 | None | 0.8445 | 1.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 9 | 9 | None | 0.6856 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 8 | 8 | None | -1.18 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 8 | 8 | None | -1.32 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 6 | 6 | None | -3.2833 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.65)` | 4 | 4 | None | -0.65 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 4 | 4 | None | -0.77 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 4 | 4 | None | -1.05 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-2.77)` | 4 | 4 | None | -2.77 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 4 | 4 | None | -0.6 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'no_natural_sample', 'observation_reason': 'pipeline_artifact_present_without_overnight_activity', 'source_artifact_present': True, 'overnight_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

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
