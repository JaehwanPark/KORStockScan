# Swing Strategy Discovery EV - 2026-06-08

- generated_at: `2026-06-08T17:05:22`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `232` / `1562` / `1562`
- labeled_sample_count: `52`
- pending_future_quote_count: `1455`
- bottom_rebound_policy_exit_row_count: `202`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 198, 'expired_entry_no_trigger': 1, 'labeled': 3}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `7`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 334, 'PENDING_ENTRY': 1121, 'EXITED': 52, 'EXPIRED': 55}, 'label_status_counts': {'pending_future_quotes': 1455, 'labeled': 52, 'expired_entry_no_trigger': 55}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 198, 'expired_entry_no_trigger': 1, 'labeled': 3}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 198, 'matured_no_entry': 1, 'matured_labeled': 3}, 'bottom_rebound_pending_future_quote_count': 198, 'bottom_rebound_labeled_sample_count': 3, 'bottom_rebound_expired_entry_count': 1, 'maturity_status_counts': {'pending_future_quotes': 1455, 'matured_labeled': 52, 'matured_no_entry': 55}, 'entry_reason_counts': {'missing_next_quote': 980, 'bottom_rebound_atr_pullback_touched': 26, 'bottom_rebound_atr_pullback_not_touched': 8, 'pullback_limit_touched': 135, 'breakout_not_touched': 86, 'gap_fade_condition_not_met': 55, 'next_open': 120, 'pullback_not_touched': 45, 'breakout_trigger_touched': 34, 'gap_fade_limit_touched': 5, 'bottom_rebound_next_open': 34, 'bottom_rebound_signal_close_retest_touched': 32, 'bottom_rebound_signal_close_retest_not_touched': 2}, 'policy_exit_reason_counts': {'missing_next_quote': 980, 'need_10_quotes': 269, 'bottom_rebound_atr_pullback_not_touched': 8, 'mae_stop_touched': 44, 'breakout_not_touched': 86, 'gap_fade_condition_not_met': 55, 'need_5_quotes': 65, 'pullback_not_touched': 45, 'trailing_after_mfe_stop': 8, 'bottom_rebound_signal_close_retest_not_touched': 2}, 'source_quality_status_counts': {'pending_future_quotes': 1455, 'ok': 107}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `8` | `11.560867` | `2.285546` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 2, 'total_row_count': 24, 'entry_fill_rate': 0.083333, 'expired_rate': 0.083333, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.2, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -7.901677}`
- discovery_combined: `{'sample_count': 50, 'source_quality_adjusted_ev_pct': -0.113995}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `4` | `9.737609` | `4.013507` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `22` | `-1.459211` | `-3.0` | `0.045455` |
| `wick_stop_recovered_close_above_stop` | `26` | `-1.984815` | `-3.0` | `0.115385` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `2` | `7.33893` | `9.737996` | `1.0` |
| `below_entry_recovery_observation` | `2` | `2.82784` | `3.229747` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `22` | `-1.459211` | `-3.0` | `0.045455` |
| `pullback_retest_observation` | `26` | `-1.984815` | `-3.0` | `0.115385` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Other Financial Intermediation` | `10` | `-3.0` | `-3.0` |
| `theme_tags` | `-` | `15` | `-3.0` | `-3.0` |
| `position_tag` | `MIDDLE` | `16` | `-1.10704` | `-3.0` |
| `position_tag` | `BREAKOUT` | `14` | `-1.007187` | `-3.0` |
| `block_reason` | `no_block_observed` | `46` | `-0.665136` | `-3.0` |
| `position_tag` | `nan` | `13` | `-0.512868` | `-3.0` |
| `volatility_bucket` | `low` | `52` | `-0.238484` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
