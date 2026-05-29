# Swing Strategy Discovery EV - 2026-05-29

- generated_at: `2026-05-29T16:47:14`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `482` / `3604` / `3604`
- labeled_sample_count: `59`
- pending_future_quote_count: `3033`
- bottom_rebound_policy_exit_row_count: `292`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 289, 'expired_entry_no_trigger': 3}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `6`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 2264, 'ENTERED': 769, 'EXPIRED': 512, 'EXITED': 59}, 'label_status_counts': {'pending_future_quotes': 3033, 'expired_entry_no_trigger': 512, 'labeled': 59}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 289, 'expired_entry_no_trigger': 3}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 289, 'matured_no_entry': 3}, 'bottom_rebound_pending_future_quote_count': 289, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 3, 'maturity_status_counts': {'pending_future_quotes': 3033, 'matured_no_entry': 512, 'matured_labeled': 59}, 'entry_reason_counts': {'next_open': 588, 'pullback_not_touched': 780, 'breakout_trigger_touched': 56, 'breakout_not_touched': 532, 'gap_fade_condition_not_met': 279, 'missing_next_quote': 1150, 'pullback_limit_touched': 102, 'gap_fade_limit_touched': 15, 'bottom_rebound_next_open': 34, 'bottom_rebound_signal_close_retest_touched': 33, 'bottom_rebound_atr_pullback_not_touched': 34, 'bottom_rebound_signal_close_retest_not_touched': 1}, 'policy_exit_reason_counts': {'need_10_quotes': 460, 'pullback_not_touched': 780, 'trailing_after_mfe_stop': 16, 'breakout_not_touched': 532, 'gap_fade_condition_not_met': 279, 'need_5_quotes': 309, 'mae_stop_touched': 43, 'missing_next_quote': 1150, 'bottom_rebound_atr_pullback_not_touched': 34, 'bottom_rebound_signal_close_retest_not_touched': 1}, 'source_quality_status_counts': {'pending_future_quotes': 3033, 'ok': 571}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `16` | `10.691952` | `4.859446` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 0, 'total_row_count': 24, 'entry_fill_rate': 0.0, 'expired_rate': 0.0, 'equal_weight_avg_final_return_pct': 0.0, 'notional_weighted_ev_pct': 0.0, 'source_quality_adjusted_ev_pct': 0.0, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': None, 'mae_p90_pct': None}`
- discovery_combined: `{'sample_count': 59, 'source_quality_adjusted_ev_pct': 0.51646}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `10` | `10.422328` | `-3.0` | `0.8` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `35` | `-0.273876` | `-3.0` | `0.228571` |
| `close_below_stop` | `14` | `-3.0` | `-3.0` | `0.0` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `9` | `10.422328` | `-3.0` | `0.777778` |
| `below_entry_recovery_observation` | `1` | `0.402101` | `2.010505` | `1.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `35` | `-0.273876` | `-3.0` | `0.228571` |
| `invalidation_observation` | `14` | `-3.0` | `-3.0` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `8` | `-1.250042` | `-3.0` |
| `position_tag` | `MIDDLE` | `19` | `-0.404199` | `-3.0` |
| `block_reason` | `blocked_swing_gap` | `7` | `-0.325786` | `-3.0` |
| `theme_tags` | `-` | `21` | `-0.322392` | `-3.0` |
| `position_tag` | `BREAKOUT` | `25` | `-0.003395` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
