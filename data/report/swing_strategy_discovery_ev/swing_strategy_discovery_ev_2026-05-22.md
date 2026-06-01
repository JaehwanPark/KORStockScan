# Swing Strategy Discovery EV - 2026-05-22

- generated_at: `2026-06-01T18:28:57`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `150` / `1200` / `1200`
- labeled_sample_count: `22`
- pending_future_quote_count: `558`
- bottom_rebound_policy_exit_row_count: `0`
- bottom_rebound_label_status_counts: `{}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `0`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 320, 'EXPIRED': 620, 'EXITED': 22, 'PENDING_ENTRY': 238}, 'label_status_counts': {'expired_entry_no_trigger': 620, 'pending_future_quotes': 558, 'labeled': 22}, 'bottom_rebound_label_status_counts': {}, 'bottom_rebound_maturity_status_counts': {}, 'bottom_rebound_pending_future_quote_count': 0, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'matured_no_entry': 620, 'pending_future_quotes': 558, 'matured_labeled': 22}, 'entry_reason_counts': {'pullback_not_touched': 444, 'breakout_not_touched': 270, 'gap_fade_condition_not_met': 144, 'next_open': 300, 'breakout_trigger_touched': 30, 'gap_fade_limit_touched': 6, 'pullback_limit_touched': 6}, 'policy_exit_reason_counts': {'pullback_not_touched': 444, 'breakout_not_touched': 270, 'gap_fade_condition_not_met': 144, 'need_10_quotes': 164, 'need_5_quotes': 156, 'mae_stop_touched': 12, 'trailing_after_mfe_stop': 10}, 'source_quality_status_counts': {'ok': 642, 'pending_future_quotes': 558}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `10` | `11.436283` | `3.5418` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 22, 'source_quality_adjusted_ev_pct': 3.525816}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `3` | `25.510967` | `13.013766` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `15` | `1.367459` | `-3.0` | `0.4` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `4` | `-0.722952` | `-3.0` | `0.25` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `3` | `25.510967` | `13.013766` | `1.0` |
| `pullback_retest_observation` | `15` | `1.367459` | `-3.0` | `0.4` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `below_entry_recovery_observation` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `4` | `-0.722952` | `-3.0` | `0.25` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| - | - | 0 | - | - |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
