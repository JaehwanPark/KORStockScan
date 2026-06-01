# Swing Strategy Discovery EV - 2026-05-27

- generated_at: `2026-06-01T18:40:33`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `325` / `2454` / `2454`
- labeled_sample_count: `39`
- pending_future_quote_count: `1648`
- bottom_rebound_policy_exit_row_count: `126`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 123, 'expired_entry_no_trigger': 3}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `2`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 767, 'ENTERED': 708, 'EXITED': 39, 'PENDING_ENTRY': 940}, 'label_status_counts': {'expired_entry_no_trigger': 767, 'pending_future_quotes': 1648, 'labeled': 39}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 123, 'expired_entry_no_trigger': 3}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 123, 'matured_no_entry': 3}, 'bottom_rebound_pending_future_quote_count': 123, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 3, 'maturity_status_counts': {'matured_no_entry': 767, 'pending_future_quotes': 1648, 'matured_labeled': 39}, 'entry_reason_counts': {'breakout_not_touched': 542, 'next_open': 588, 'pullback_not_touched': 843, 'gap_fade_condition_not_met': 285, 'breakout_trigger_touched': 46, 'gap_fade_limit_touched': 9, 'pullback_limit_touched': 39, 'bottom_rebound_next_open': 34, 'bottom_rebound_signal_close_retest_touched': 27, 'bottom_rebound_atr_pullback_not_touched': 30, 'bottom_rebound_atr_pullback_touched': 4, 'bottom_rebound_signal_close_retest_not_touched': 7}, 'policy_exit_reason_counts': {'breakout_not_touched': 542, 'need_5_quotes': 303, 'need_10_quotes': 405, 'pullback_not_touched': 843, 'gap_fade_condition_not_met': 285, 'mae_stop_touched': 26, 'trailing_after_mfe_stop': 13, 'bottom_rebound_atr_pullback_not_touched': 30, 'bottom_rebound_signal_close_retest_not_touched': 7}, 'source_quality_status_counts': {'ok': 806, 'pending_future_quotes': 1648}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `13` | `12.283896` | `5.403813` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 39, 'source_quality_adjusted_ev_pct': 2.14599}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `3` | `23.002225` | `9.69814` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `26` | `1.967871` | `-3.0` | `0.346154` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `10` | `-1.877659` | `-3.0` | `0.1` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `3` | `23.002225` | `9.69814` | `1.0` |
| `pullback_retest_observation` | `26` | `1.967871` | `-3.0` | `0.346154` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `below_entry_recovery_observation` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `10` | `-1.877659` | `-3.0` | `0.1` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `position_tag` | `BOTTOM` | `5` | `-1.861551` | `-3.0` |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `5` | `-1.739503` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
