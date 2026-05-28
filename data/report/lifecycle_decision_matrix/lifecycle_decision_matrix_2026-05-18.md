# Lifecycle Decision Matrix - 2026-05-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-18`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `489`
- source_rows_total: `489`
- retained_rows: `489`
- dropped_rows_by_source: `{}`
- joined_rows: `434`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `7` / `5`
- exit_bucket_count/workorders: `8` / `0`
- scale_in_bucket_actionable_count: `37`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `11`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 477, 'missing_holding': 477, 'missing_exit': 478, 'missing_entry': 431}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 49 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 3 | 2 | -1.4534 | 0.1333 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 3 | 2 | -1.8724 | 0.1333 | `hold_sample` | `EXIT` | False |
| `scale_in` | 432 | 428 | -0.8106 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2 | 2 | -1.8724 | 0.2 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 480, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 489, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 49, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 49}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 3, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 3}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 3, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 3}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 432, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 432}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 2, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_submit': 477, 'missing_holding': 477, 'missing_exit': 478, 'missing_entry': 431}, 'bucket_count': 11, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 427 | 425 | -0.4237 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:2a3fd5bd00` | 1 | 1 | -2.4476 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f453f7b6dd` | 1 | 1 | -1.2972 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | -55.622 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:5c45db6e34` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:83c74e766d` | 28 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:6b5a9dbd28` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:b66da9efdf` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:5afa7ecf4e` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:fcd588ff6c` | 12 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bbed60de0b` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 49, 'bucket_count': 32, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 49 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 11 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1000_1200` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 9 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1000_1200` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=blocked_ai_score|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 49 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_unknown` | 49 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 22 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 27 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_60_62` | 29 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 3, 'bucket_count': 24, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3 | 2 | -1.4534 | `keep_collecting` |
| `broker_order_forbidden` | `broker_order_forbidden_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 1 | 1 | -2.2414 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=true|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.6654 | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 3 | 2 | -1.4534 | `source_quality_workorder` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 2 | 1 | -2.2414 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 1 | -0.6654 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 2 | 1 | -2.2414 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 1 | 1 | -0.6654 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 2 | 1 | -2.2414 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 1 | 1 | -0.6654 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 2 | 1 | -2.2414 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1 | 1 | -0.6654 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 2 | 1 | -2.2414 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1 | 1 | -0.6654 | `keep_collecting` |
| `would_limit_fill` | `false` | 1 | 1 | -2.2414 | `keep_collecting` |
| `would_limit_fill` | `true` | 1 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1 | 1 | -0.6654 | `source_quality_workorder` |

### Submit Bucket Workorders

- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 3, 'source_row_count': 3, 'bucket_count': 7, 'joined_sample': 10, 'source_quality_adjusted_ev_pct': -1.8724, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {'not_applicable': 2, 'join_gap': 4, 'missing_source_field': 2}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 2 | 2 | -1.8724 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 3 | 2 | -1.8724 | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 3 | 2 | -1.8724 | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3 | 2 | -1.8724 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -1.8724 | `hold_sample` |
| `profit_band` | `profit_unknown` | 1 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `holding_action_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 2, 'source_row_count': 2, 'bucket_count': 8, 'joined_sample': 10, 'source_quality_adjusted_ev_pct': -1.8724, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.4476 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.2972 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 1 | 1 | -2.4476 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | -1.2972 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 1 | 1 | -2.4476 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -1.2972 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2 | 2 | -1.8724 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -1.8724 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 432, 'bucket_count': 112, 'actionable_bucket_count': 37, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 429, 'PYRAMID': 3}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 332 | 332 | -0.4758 | -0.5482 | 0.1566 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 64 | 64 | -0.2687 | -0.3358 | 0.25 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 17 | 17 | -0.5039 | -0.6065 | 0.2353 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 8 | 8 | 0.331 | 0.3075 | 0.625 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_lt60` | 7 | 7 | -23.6917 | -29.6371 | 0.2857 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 4 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 432 | 428 | -0.8106 | -0.9785 | 0.1846 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 429 | 427 | -0.6267 | -0.7487 | 0.185 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 3 | 1 | -79.326 | -99.1 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 386 | 386 | -0.6423 | -0.7773 | 0.2047 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 41 | 41 | -0.4798 | -0.4798 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 1 | 1 | -79.326 | -99.1 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PRICE_GUARD` | 2 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 2 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `scale_in_probe_blocked` | 131 | 131 | -0.4414 | -0.6106 | 0.1908 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 63 | 63 | -0.4002 | -0.4002 | 0.0476 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scale_in_gate_blocked` | 41 | 41 | -0.213 | -0.3868 | 0.0732 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 20 | 20 | -0.79 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 19 | 19 | -1.16 | -1.16 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.35)` | 19 | 19 | -1.35 | -1.35 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.70)` | 17 | 17 | 0.7 | 0.7 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 16 | 16 | -0.98 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.04)` | 14 | 14 | -0.04 | -0.04 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.33)` | 11 | 11 | 0.33 | 0.33 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(0.14)` | 9 | 9 | 0.14 | 0.14 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.89)` | 7 | 7 | 0.89 | 0.89 | 1.0 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 308 | 308 | -0.3599 | -0.4294 | 0.2468 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 61 | 61 | -0.8609 | -0.9677 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_180_600s` | 35 | 35 | -0.3285 | -0.3571 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 17 | 17 | -0.4588 | -0.5418 | 0.0588 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_lt020s` | 7 | 7 | -23.4666 | -29.4014 | 0.2857 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 255 | 251 | -0.4394 | -0.4394 | 0.2032 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 75 | 75 | -0.347 | -0.4864 | 0.2 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 54 | 54 | -3.8991 | -4.7935 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 48 | 48 | -0.0014 | -0.2748 | 0.2708 | `hold_no_edge` |
| `price_guard_reason` | `price_guard_none` | 430 | 428 | -0.8106 | -0.9785 | 0.1846 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 168 | 168 | -1.9701 | -2.3258 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 145 | 145 | -0.3888 | -0.4583 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 101 | 101 | 0.2664 | 0.2477 | 0.6436 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.9651 | 0.9543 | 1.0 | `candidate_recovery_or_relax` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `scale_in_probe_blocked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `add_judgment_locked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_reason` / `pnl_out_of_range(-0.79)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `blocker_reason` / `pnl_out_of_range(-1.16)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_13`: `blocker_reason` / `pnl_out_of_range(-1.35)` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `scale_in_probe_blocked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `add_judgment_locked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {}}`

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
