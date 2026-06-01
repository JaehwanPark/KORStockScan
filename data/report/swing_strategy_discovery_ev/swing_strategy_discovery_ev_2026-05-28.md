# Swing Strategy Discovery EV - 2026-05-28

- generated_at: `2026-06-01T18:46:22`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `432` / `3204` / `3204`
- labeled_sample_count: `66`
- pending_future_quote_count: `2299`
- bottom_rebound_policy_exit_row_count: `292`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 280, 'expired_entry_no_trigger': 11, 'labeled': 1}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `2`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 1053, 'EXPIRED': 839, 'EXITED': 66, 'PENDING_ENTRY': 1246}, 'label_status_counts': {'expired_entry_no_trigger': 839, 'pending_future_quotes': 2299, 'labeled': 66}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 280, 'expired_entry_no_trigger': 11, 'labeled': 1}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 280, 'matured_no_entry': 11, 'matured_labeled': 1}, 'bottom_rebound_pending_future_quote_count': 280, 'bottom_rebound_labeled_sample_count': 1, 'bottom_rebound_expired_entry_count': 11, 'maturity_status_counts': {'matured_no_entry': 839, 'pending_future_quotes': 2299, 'matured_labeled': 66}, 'entry_reason_counts': {'breakout_not_touched': 678, 'pullback_not_touched': 993, 'next_open': 750, 'gap_fade_condition_not_met': 353, 'breakout_trigger_touched': 72, 'gap_fade_limit_touched': 22, 'pullback_limit_touched': 132, 'bottom_rebound_next_open': 68, 'bottom_rebound_signal_close_retest_touched': 60, 'bottom_rebound_atr_pullback_not_touched': 53, 'bottom_rebound_signal_close_retest_not_touched': 8, 'bottom_rebound_atr_pullback_touched': 15}, 'policy_exit_reason_counts': {'breakout_not_touched': 678, 'pullback_not_touched': 993, 'need_10_quotes': 656, 'gap_fade_condition_not_met': 353, 'need_5_quotes': 397, 'mae_stop_touched': 45, 'trailing_after_mfe_stop': 21, 'bottom_rebound_atr_pullback_not_touched': 53, 'bottom_rebound_signal_close_retest_not_touched': 8}, 'source_quality_status_counts': {'ok': 905, 'pending_future_quotes': 2299}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `21` | `11.817709` | `3.728804` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 1, 'total_row_count': 24, 'entry_fill_rate': 0.041667, 'expired_rate': 0.125, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -0.6, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -12.313053}`
- discovery_combined: `{'sample_count': 65, 'source_quality_adjusted_ev_pct': 2.114707}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `7` | `19.850184` | `5.735432` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `43` | `1.32087` | `-3.0` | `0.302326` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `16` | `-2.415395` | `-3.0` | `0.0625` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `4` | `20.580604` | `8.542394` | `1.0` |
| `below_entry_recovery_observation` | `3` | `9.307019` | `6.76836` | `1.0` |
| `pullback_retest_observation` | `43` | `1.32087` | `-3.0` | `0.302326` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `16` | `-2.415395` | `-3.0` | `0.0625` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Basic Chemicals` | `7` | `-1.708779` | `-3.0` |
| `position_tag` | `MIDDLE` | `22` | `-1.377592` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
