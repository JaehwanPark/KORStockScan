# Swing Strategy Discovery EV - 2026-06-05

- generated_at: `2026-06-05T18:01:42`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `143` / `982` / `982`
- labeled_sample_count: `0`
- pending_future_quote_count: `982`
- bottom_rebound_policy_exit_row_count: `110`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 110}`
- top_surviving_arm: `-`
- avoid_bucket_count: `0`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 982}, 'label_status_counts': {'pending_future_quotes': 982}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 110}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 110}, 'bottom_rebound_pending_future_quote_count': 110, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'pending_future_quotes': 982}, 'entry_reason_counts': {'missing_next_quote': 982}, 'policy_exit_reason_counts': {'missing_next_quote': 982}, 'source_quality_status_counts': {'pending_future_quotes': 982}}`
- warnings: `['pending_future_quotes', 'sample_floor_not_met', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| - | 0 | - | - | - |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 0, 'total_row_count': 16, 'entry_fill_rate': 0.0, 'expired_rate': 0.0, 'equal_weight_avg_final_return_pct': 0.0, 'notional_weighted_ev_pct': 0.0, 'source_quality_adjusted_ev_pct': 0.0, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': None, 'mae_p90_pct': None}`
- discovery_combined: `{'sample_count': 0, 'source_quality_adjusted_ev_pct': 0.0}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| - | - | 0 | - | - |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
