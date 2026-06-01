# Swing Strategy Discovery EV - 2026-05-29

- generated_at: `2026-06-01T18:53:59`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `544` / `3954` / `3954`
- labeled_sample_count: `54`
- pending_future_quote_count: `3055`
- bottom_rebound_policy_exit_row_count: `396`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 385, 'expired_entry_no_trigger': 11}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `1`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 2058, 'ENTERED': 997, 'EXPIRED': 845, 'EXITED': 54}, 'label_status_counts': {'expired_entry_no_trigger': 845, 'pending_future_quotes': 3055, 'labeled': 54}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 385, 'expired_entry_no_trigger': 11}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 385, 'matured_no_entry': 11}, 'bottom_rebound_pending_future_quote_count': 385, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 11, 'maturity_status_counts': {'matured_no_entry': 845, 'pending_future_quotes': 3055, 'matured_labeled': 54}, 'entry_reason_counts': {'pullback_not_touched': 1035, 'breakout_not_touched': 694, 'gap_fade_condition_not_met': 357, 'next_open': 750, 'breakout_trigger_touched': 56, 'missing_next_quote': 750, 'gap_fade_limit_touched': 18, 'pullback_limit_touched': 90, 'bottom_rebound_next_open': 68, 'bottom_rebound_signal_close_retest_touched': 60, 'bottom_rebound_atr_pullback_not_touched': 59, 'bottom_rebound_signal_close_retest_not_touched': 8, 'bottom_rebound_atr_pullback_touched': 9}, 'policy_exit_reason_counts': {'pullback_not_touched': 1035, 'breakout_not_touched': 694, 'gap_fade_condition_not_met': 357, 'need_5_quotes': 393, 'need_10_quotes': 604, 'trailing_after_mfe_stop': 20, 'missing_next_quote': 750, 'mae_stop_touched': 34, 'bottom_rebound_atr_pullback_not_touched': 59, 'bottom_rebound_signal_close_retest_not_touched': 8}, 'source_quality_status_counts': {'ok': 899, 'pending_future_quotes': 3055}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `20` | `10.6245` | `2.715991` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 1, 'total_row_count': 24, 'entry_fill_rate': 0.041667, 'expired_rate': 0.125, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -0.6, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -13.60892}`
- discovery_combined: `{'sample_count': 53, 'source_quality_adjusted_ev_pct': 2.407446}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `5` | `22.779785` | `7.39685` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `39` | `1.678588` | `-3.0` | `0.358974` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `10` | `-2.262523` | `-3.0` | `0.1` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `2` | `13.71139` | `12.561078` | `1.0` |
| `below_entry_recovery_observation` | `3` | `9.881893` | `7.134494` | `1.0` |
| `pullback_retest_observation` | `39` | `1.678588` | `-3.0` | `0.358974` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `10` | `-2.262523` | `-3.0` | `0.1` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `position_tag` | `MIDDLE` | `14` | `-0.964688` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
