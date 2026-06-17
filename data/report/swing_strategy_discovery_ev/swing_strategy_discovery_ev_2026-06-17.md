# Swing Strategy Discovery EV - 2026-06-17

- generated_at: `2026-06-17T16:23:02`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `860` / `5513` / `5513`
- labeled_sample_count: `457`
- pending_future_quote_count: `3980`
- bottom_rebound_policy_exit_row_count: `961`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 803, 'expired_entry_no_trigger': 144, 'labeled': 14}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `8`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 1076, 'PENDING_ENTRY': 1835, 'ENTERED': 2145, 'EXITED': 457}, 'label_status_counts': {'expired_entry_no_trigger': 1076, 'pending_future_quotes': 3980, 'labeled': 457}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 803, 'expired_entry_no_trigger': 144, 'labeled': 14}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 803, 'matured_no_entry': 144, 'matured_labeled': 14}, 'bottom_rebound_pending_future_quote_count': 803, 'bottom_rebound_labeled_sample_count': 14, 'bottom_rebound_expired_entry_count': 144, 'maturity_status_counts': {'matured_no_entry': 1076, 'pending_future_quotes': 3980, 'matured_labeled': 457}, 'entry_reason_counts': {'gap_fade_condition_not_met': 430, 'pullback_not_touched': 873, 'breakout_trigger_touched': 642, 'breakout_not_touched': 296, 'next_open': 938, 'bottom_rebound_atr_pullback_not_touched': 196, 'bottom_rebound_next_open': 259, 'missing_next_quote': 984, 'bottom_rebound_signal_close_retest_touched': 127, 'pullback_limit_touched': 534, 'gap_fade_limit_touched': 39, 'bottom_rebound_atr_pullback_touched': 63, 'bottom_rebound_signal_close_retest_not_touched': 132}, 'policy_exit_reason_counts': {'gap_fade_condition_not_met': 430, 'pullback_not_touched': 873, 'need_10_quotes': 1637, 'breakout_not_touched': 296, 'need_5_quotes': 508, 'bottom_rebound_atr_pullback_not_touched': 196, 'missing_next_quote': 984, 'mae_stop_touched': 254, 'trailing_after_mfe_stop': 203, 'bottom_rebound_signal_close_retest_not_touched': 132}, 'source_quality_status_counts': {'ok': 1533, 'pending_future_quotes': 3980}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `203` | `8.582847` | `2.601657` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 2, 'total_row_count': 24, 'entry_fill_rate': 0.083333, 'expired_rate': 0.5, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.2, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -10.056927}`
- discovery_combined: `{'sample_count': 455, 'source_quality_adjusted_ev_pct': 2.830028}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `136` | `7.959457` | `-3.0` | `0.867647` |
| `wick_stop_recovered_close_above_stop` | `204` | `0.702775` | `-3.0` | `0.279412` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `117` | `-0.192858` | `-3.0` | `0.239316` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `70` | `11.97841` | `4.066252` | `0.985714` |
| `premium_entry_continuation_observation` | `3` | `6.296252` | `4.452765` | `1.0` |
| `below_entry_recovery_observation` | `38` | `3.676492` | `-3.0` | `0.789474` |
| `neutral_location_observation` | `22` | `3.260467` | `-3.0` | `0.727273` |
| `pullback_retest_observation` | `204` | `0.702775` | `-3.0` | `0.279412` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `117` | `-0.192858` | `-3.0` | `0.239316` |
| `discount_entry_observation` | `3` | `-1.8` | `-3.0` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `10` | `-3.0` | `-3.0` |
| `sector` | `Computer programming, System Integration and Management Services` | `7` | `-3.0` | `-3.0` |
| `sector` | `Software Development and Supply` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `반도체_생산` | `11` | `-3.0` | `-3.0` |
| `theme_tags` | `자원개발 E&P` | `5` | `-1.840573` | `-3.0` |
| `sector` | `Activities Auxiliary to Financial Service Activities` | `10` | `-0.616867` | `-3.0` |
| `theme_tags` | `증권` | `9` | `-0.374822` | `-3.0` |
| `theme_tags` | `PCB(인쇄회로기판)` | `6` | `-0.139125` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
