# Swing Strategy Discovery EV - 2026-05-20

- generated_at: `2026-06-01T15:45:59`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `50` / `400` / `400`
- labeled_sample_count: `13`
- pending_future_quote_count: `128`
- bottom_rebound_policy_exit_row_count: `0`
- bottom_rebound_label_status_counts: `{}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `0`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXITED': 13, 'EXPIRED': 259, 'ENTERED': 128}, 'label_status_counts': {'labeled': 13, 'expired_entry_no_trigger': 259, 'pending_future_quotes': 128}, 'bottom_rebound_label_status_counts': {}, 'bottom_rebound_maturity_status_counts': {}, 'bottom_rebound_pending_future_quote_count': 0, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'matured_labeled': 13, 'matured_no_entry': 259, 'pending_future_quotes': 128}, 'entry_reason_counts': {'breakout_trigger_touched': 16, 'breakout_not_touched': 84, 'gap_fade_condition_not_met': 49, 'gap_fade_limit_touched': 1, 'next_open': 100, 'pullback_not_touched': 126, 'pullback_limit_touched': 24}, 'policy_exit_reason_counts': {'trailing_after_mfe_stop': 6, 'breakout_not_touched': 84, 'need_10_quotes': 77, 'mae_stop_touched': 7, 'gap_fade_condition_not_met': 49, 'need_5_quotes': 51, 'pullback_not_touched': 126}, 'source_quality_status_counts': {'ok': 272, 'pending_future_quotes': 128}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `6` | `7.609118` | `4.500884` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 13, 'source_quality_adjusted_ev_pct': 2.424439}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `close_below_stop` | `3` | `2.247702` | `-3.0` | `0.333333` |
| `no_touch` | `1` | `1.710859` | `8.554296` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `9` | `1.634663` | `-3.0` | `0.444444` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `invalidation_observation` | `3` | `2.247702` | `-3.0` | `0.333333` |
| `below_entry_recovery_observation` | `1` | `1.710859` | `8.554296` | `1.0` |
| `pullback_retest_observation` | `9` | `1.634663` | `-3.0` | `0.444444` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `momentum_chase_observation` | `0` | `0.0` | `None` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| - | - | 0 | - | - |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
