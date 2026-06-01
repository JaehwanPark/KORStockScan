# Lifecycle Decision Matrix - 2026-06-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-01_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `23223`
- source_rows_total: `42018`
- retained_rows: `23223`
- dropped_rows_by_source: `{'dedupe': 18795}`
- joined_rows: `22128`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `26`
- entry_bucket_runtime_candidate_count: `10`
- holding_bucket_count/workorders: `36` / `10`
- exit_bucket_count/workorders: `59` / `10`
- scale_in_bucket_actionable_count: `255`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `1`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `120`
- lifecycle_flow_complete_count: `108`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.005`
- incomplete_flow_reason_counts: `{'missing_submit': 21451, 'missing_holding': 21442, 'missing_exit': 20817, 'missing_entry': 20929, 'postclose_exit_without_entry': 650, 'candidate_id_only': 21077, 'sim_record_id_only': 339}`
- bucket_directed_sim_probe: `{'observed_row_count': 2038, 'matched_row_count': 491, 'background_row_count': 1547, 'matched_unique_source_bucket_count': 5, 'match_status_counts': {'matched': 491, 'no_match': 880, 'not_instrumented': 667}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 491}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 919 | 218 | 1.5834 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 382 | 349 | -0.6564 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 363 | 349 | -0.9015 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 20571 | 20569 | -0.3671 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 988 | 643 | -0.951 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 21575, 'complete_flow_count': 108, 'incomplete_flow_count': 21467, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 23223, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.005, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 919, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 419, 'candidate_id': 500}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 382, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 382}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 363, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 349, 'exact_sim_record_id': 14}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 20571, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 20232, 'exact_sim_record_id': 339}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 988, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 335, 'exact_sim_record_id': 308, 'candidate_id': 345}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 919, 'submit': 382, 'holding': 363, 'exit': 988}, 'incomplete_flow_reason_counts': {'missing_submit': 21451, 'missing_holding': 21442, 'missing_exit': 20817, 'missing_entry': 20929, 'postclose_exit_without_entry': 650, 'candidate_id_only': 21077, 'sim_record_id_only': 339}, 'bucket_count': 120, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7c897ec6ef` | 6 | 6 | -2.3006 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:93f13405b3` | 6 | 6 | -0.8792 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:07dd4b972c` | 5 | 5 | -0.7142 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:438a0575a6` | 5 | 5 | -0.3313 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b72b8d0720` | 4 | 4 | -1.5819 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3799fc10bf` | 3 | 3 | -0.9324 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:f10228dfd1` | 3 | 3 | -1.7844 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:3fb7337b6e` | 2 | 2 | -1.943 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:24202c8c35` | 2 | 2 | -0.2676 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:cbc2ec64ca` | 2 | 2 | 0.8175 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:77aa085c35` | 2 | 2 | 0.5734 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e1711e47a2` | 2 | 2 | -2.2915 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e897ec274e` | 2 | 2 | -0.9836 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:68712b8877` | 2 | 2 | -1.733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:c8ca2bc9db` | 2 | 2 | -2.2709 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:32b574b47c` | 2 | 2 | -0.1189 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:e276c43353` | 1 | 1 | -1.5561 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7567ae9373` | 1 | 1 | -1.1526 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:dd960db27f` | 1 | 1 | -1.4316 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:c81ac13c6b` | 1 | 1 | -0.9492 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 919, 'bucket_count': 206, 'actionable_bucket_count': 26, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 166 | 166 | 2.1479 | 3.589 | 0.6084 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 404 | 41 | -0.1008 | -1.3678 | 0.1707 | `hold_no_edge` |
| `chosen_action` | `BUY_NOW` | 13 | 11 | -0.6572 | 0.0245 | 0.4545 | `candidate_tighten_or_exclude` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 61 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 273 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 19 | 19 | 2.2955 | 3.6407 | 0.6316 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 16 | 16 | 2.7605 | 4.7496 | 0.5625 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 13 | 13 | 3.4644 | 6.1135 | 0.7692 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 11 | 11 | 1.2473 | 1.6297 | 0.6364 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 11 | 11 | 0.6196 | 0.8048 | 0.7273 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 11 | 11 | 1.9222 | 3.7065 | 0.5455 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_0900_1000` | 9 | 9 | -0.719 | -0.9686 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 70 | 7 | 0.5005 | -1.5814 | 0.1429 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_0900_1000` | 7 | 7 | 1.1185 | 1.843 | 0.4286 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1400_close` | 6 | 6 | 3.3479 | 5.0603 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1400_close` | 6 | 6 | 1.1419 | 1.7426 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1200_1400` | 6 | 6 | 2.4629 | 3.5074 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1000_1200` | 13 | 5 | -0.0351 | -2.0 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 30 | 5 | -0.7152 | -0.296 | 0.4 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 867 | 166 | 2.1479 | 3.589 | 0.6084 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 31 | 31 | -0.0303 | -1.8835 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | -0.0085 | 2.1967 | 1.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 166 | 166 | 2.1479 | 3.589 | 0.6084 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 419 | 52 | -0.2185 | -1.0733 | 0.2308 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_normal` | 87 | 87 | 2.1265 | 3.4478 | 0.6092 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 251 | 40 | 0.0984 | -0.8127 | 0.275 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_watch` | 38 | 38 | 2.5485 | 4.4065 | 0.5526 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 26 | 26 | 2.644 | 4.5089 | 0.7692 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 91 | 13 | 0.8926 | 1.1296 | 0.5385 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 38 | 11 | -1.4338 | -1.8727 | 0.0909 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 266 | 112 | 1.5129 | 2.7489 | 0.5804 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 86 | 59 | 2.7847 | 4.3972 | 0.6102 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 441 | 26 | -0.217 | -1.5446 | 0.1538 | `hold_no_edge` |
| `score_band` | `score_63_65` | 53 | 17 | 0.9412 | 1.2367 | 0.4706 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 166 | 166 | 2.1479 | 3.589 | 0.6084 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 293 | 52 | -0.2185 | -1.0733 | 0.2308 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 500 | 166 | 2.1479 | 3.589 | 0.6084 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 325 | 50 | -0.205 | -1.0264 | 0.24 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 173 | 140 | 2.3409 | 3.9294 | 0.6286 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_10`: `liquidity_bucket` / `liquidity_high` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `overbought_bucket` / `overbought_proxy_normal` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `overbought_bucket` / `overbought_proxy_watch` -> `candidate_recovery_or_relax`
- `entry_bucket_13`: `overbought_bucket` / `overbought_proxy_chase_risk` -> `candidate_recovery_or_relax`
- `entry_bucket_16`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_17`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_19`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_20`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_21`: `strength_bucket` / `strong_strength_momentum` -> `candidate_recovery_or_relax`
- `entry_bucket_22`: `strength_bucket` / `weak_strength_momentum` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `WAIT_REQUOTE` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `BUY_NOW` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 382, 'bucket_count': 70, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 365 | 349 | -0.6564 | `keep_collecting` |
| `actual_order_submitted` | `true` | 17 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 365 | 349 | -0.6564 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 17 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 153 | 153 | -0.4828 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 77 | 77 | -0.6804 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 43 | 43 | -0.1082 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 23 | 23 | -0.7707 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 13 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -0.6201 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -0.1682 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 9 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | -3.6731 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 4 | 4 | -0.1873 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -2.5133 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -3.5023 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.8499 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.0918 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=pullback_required|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 1 | 1 | 2.7764 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -3.4862 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.6695 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 349 | 349 | -0.6564 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 33 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 349 | 349 | -0.6564 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 33 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 283 | 272 | -0.7547 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 77 | 77 | -0.3092 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 22 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 272 | 272 | -0.7547 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 77 | 77 | -0.3092 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 33 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 336 | 314 | -0.4891 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 39 | 34 | -2.1712 | `keep_collecting` |
| `overbought_bucket` | `overbought_normal` | 5 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -1.6695 | `keep_collecting` |
| `overbought_bucket` | `pullback_required` | 1 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 363, 'source_row_count': 363, 'bucket_count': 36, 'joined_sample': 1745, 'source_quality_adjusted_ev_pct': -0.9015, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 135 | 135 | -1.4168 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 106 | 106 | -1.6018 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 22 | 22 | -0.0346 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 18 | 18 | 0.1133 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 16 | 16 | 0.9206 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 11 | 11 | 1.778 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 11 | 11 | -0.3617 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.201 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | 0.9013 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.2268 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 3.2749 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.4425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.355 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 2.5685 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.2951 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 349 | 349 | -0.9015 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 204 | 204 | -0.7676 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 139 | 139 | -1.1366 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 6 | 6 | -0.0073 | `hold_no_edge` |
| `holding_action` | `SELL_TODAY` | 14 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 349 | 349 | -0.9015 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 14 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 249 | 245 | -1.4937 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 34 | 34 | -0.0639 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 33 | 28 | 0.0011 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 23 | 22 | 0.9153 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 16 | 16 | 2.1846 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.3987 | `candidate_tighten_or_exclude` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 988, 'source_row_count': 988, 'bucket_count': 59, 'joined_sample': 3215, 'source_quality_adjusted_ev_pct': -0.951, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 4, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 221 | 221 | -1.1997 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 67 | 67 | -0.5531 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 51 | 51 | -2.4566 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 48 | 48 | -1.7976 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 41 | 41 | -1.2368 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 39 | 39 | -0.7798 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 38 | 38 | -1.085 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -1.5764 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 15 | 15 | -0.7383 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 13 | 13 | -0.2463 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 13 | 13 | 0.6479 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 8 | 8 | 0.1826 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.6966 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 7 | 7 | 1.3376 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 6 | 6 | 0.0801 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 5 | 5 | 0.1665 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -0.2574 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 5 | 5 | 3.0791 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | 0.0368 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.7856 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.2944 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.3025 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 4 | 4 | 0.4779 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.442 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -0.5751 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 3 | 3 | 2.1275 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 1.28 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 1 | 1 | 1.5225 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.8114 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.3054 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.0254 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.255 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 334 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 294 | 294 | -1.0151 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 145 | 145 | -1.4948 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 112 | 112 | -0.3396 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 78 | 78 | -0.7218 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 359 | 14 | -0.1404 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 294 | 294 | -1.0151 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 20571, 'bucket_count': 2400, 'actionable_bucket_count': 255, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 15404, 'PYRAMID': 5167}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 10876 | 10876 | -0.3408 | -0.4197 | 0.2708 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 3225 | 3225 | -0.3821 | -0.4581 | 0.2419 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 2757 | 2757 | -0.468 | -0.5327 | 0.1962 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 2280 | 2280 | -0.3319 | -0.4073 | 0.2439 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1431 | 1431 | -0.3952 | -0.4661 | 0.1908 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 2 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 20569 | 20569 | -0.3671 | -0.4427 | 0.2477 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `stage_rule_backfilled` | 2 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 15404 | 15403 | -0.7013 | -0.7864 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 5167 | 5166 | 0.6293 | 0.5819 | 0.9863 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 11128 | 11127 | -0.836 | -0.926 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 5167 | 5166 | 0.6293 | 0.5819 | 0.9863 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4276 | 4276 | -0.3509 | -0.423 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 4186 | 4186 | 0.5632 | 0.5127 | 0.9924 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 2925 | 2925 | -0.2316 | -0.2541 | 0.2369 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 641 | 641 | -0.4244 | -0.4526 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 339 | 339 | -0.8468 | -0.8468 | 0.0383 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 201 | 201 | 2.6572 | 2.7028 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `ok` | 178 | 178 | -1.8095 | -2.2947 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 169 | 169 | -1.1826 | -1.32 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 154 | 154 | -0.6916 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 146 | 146 | -0.8657 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 140 | 140 | -0.9632 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 138 | 138 | -0.9585 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 136 | 136 | -0.856 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 135 | 135 | -0.8265 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 135 | 135 | -1.0356 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 133 | 133 | -0.2246 | -0.2617 | 0.2481 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 126 | 126 | -0.6576 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.30)` | 120 | 120 | -1.1718 | -1.3 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 116 | 116 | -0.6732 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.34)` | 114 | 114 | -1.2123 | -1.34 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 113 | 113 | -0.624 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 111 | 111 | -0.8482 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 109 | 109 | -0.8431 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 106 | 106 | -0.7576 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 106 | 106 | -1.1037 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 105 | 105 | -0.7602 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 104 | 104 | -0.7509 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 100 | 100 | -0.8633 | -0.97 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `ai_score_source` / `score_field_backfilled` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_9`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `ai_score_source` / `score_field_backfilled` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 28, 'bucket_count': 27, 'actionable_bucket_count': 1, 'runtime_candidate_count': 0, 'workorder_count': 1, 'status_counts': {'HOLD_OVERNIGHT': 14, 'SELL_TODAY': 14}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 5 | 5 | 0.1665 | 0.222 | 0.8 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -0.7856 | -1.0475 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2944 | -0.3925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 1 | 1 | 1.5225 | 2.03 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 28 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -0.09 | -0.12 | 0.2857 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 7 | -0.1907 | -0.2543 | 0.4286 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 28 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 14 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 14 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.54 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.1665 | 0.222 | 0.8 | `hold_no_edge` |
| `peak_profit_band` | `peak_pos150_pos300` | 2 | 1 | 1.5225 | 2.03 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 28 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 10 | 5 | 0.1665 | 0.222 | 0.8 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -0.7856 | -1.0475 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 28 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |
| `stage` | `exit` | 14 | 14 | -0.1404 | -0.1871 | 0.3571 | `hold_no_edge` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
