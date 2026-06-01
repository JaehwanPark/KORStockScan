# Swing Strategy Discovery EV - 2026-05-21

- generated_at: `2026-06-01T18:23:55`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `100` / `800` / `800`
- labeled_sample_count: `20`
- pending_future_quote_count: `210`
- bottom_rebound_policy_exit_row_count: `0`
- bottom_rebound_label_status_counts: `{}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `1`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 570, 'ENTERED': 210, 'EXITED': 20}, 'label_status_counts': {'expired_entry_no_trigger': 570, 'pending_future_quotes': 210, 'labeled': 20}, 'bottom_rebound_label_status_counts': {}, 'bottom_rebound_maturity_status_counts': {}, 'bottom_rebound_pending_future_quote_count': 0, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'matured_no_entry': 570, 'pending_future_quotes': 210, 'matured_labeled': 20}, 'entry_reason_counts': {'pullback_not_touched': 300, 'gap_fade_condition_not_met': 98, 'next_open': 200, 'breakout_trigger_touched': 28, 'breakout_not_touched': 172, 'gap_fade_limit_touched': 2}, 'policy_exit_reason_counts': {'pullback_not_touched': 300, 'gap_fade_condition_not_met': 98, 'need_5_quotes': 102, 'need_10_quotes': 108, 'trailing_after_mfe_stop': 10, 'mae_stop_touched': 10, 'breakout_not_touched': 172}, 'source_quality_status_counts': {'ok': 590, 'pending_future_quotes': 210}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `10` | `11.623577` | `3.206474` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 20, 'source_quality_adjusted_ev_pct': 4.052358}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `4` | `24.287976` | `13.978144` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `9` | `0.271901` | `-3.0` | `0.444444` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `7` | `-0.500266` | `-3.0` | `0.285714` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `3` | `26.793632` | `14.708973` | `1.0` |
| `below_entry_recovery_observation` | `1` | `2.915612` | `14.578058` | `1.0` |
| `pullback_retest_observation` | `9` | `0.271901` | `-3.0` | `0.444444` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `7` | `-0.500266` | `-3.0` | `0.285714` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `7` | `-0.065012` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
