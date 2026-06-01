# Swing Strategy Discovery EV - 2026-05-26

- generated_at: `2026-06-01T18:33:33`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `234` / `1872` / `1872`
- labeled_sample_count: `36`
- pending_future_quote_count: `1132`
- bottom_rebound_policy_exit_row_count: `0`
- bottom_rebound_label_status_counts: `{}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `2`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 513, 'EXPIRED': 704, 'EXITED': 36, 'PENDING_ENTRY': 619}, 'label_status_counts': {'expired_entry_no_trigger': 704, 'pending_future_quotes': 1132, 'labeled': 36}, 'bottom_rebound_label_status_counts': {}, 'bottom_rebound_maturity_status_counts': {}, 'bottom_rebound_pending_future_quote_count': 0, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'matured_no_entry': 704, 'pending_future_quotes': 1132, 'matured_labeled': 36}, 'entry_reason_counts': {'pullback_not_touched': 675, 'next_open': 468, 'breakout_trigger_touched': 48, 'breakout_not_touched': 420, 'gap_fade_condition_not_met': 228, 'gap_fade_limit_touched': 6, 'pullback_limit_touched': 27}, 'policy_exit_reason_counts': {'pullback_not_touched': 675, 'need_10_quotes': 273, 'breakout_not_touched': 420, 'gap_fade_condition_not_met': 228, 'need_5_quotes': 240, 'mae_stop_touched': 22, 'trailing_after_mfe_stop': 14}, 'source_quality_status_counts': {'ok': 740, 'pending_future_quotes': 1132}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `14` | `10.283734` | `2.375591` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 36, 'source_quality_adjusted_ev_pct': 2.269521}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `4` | `22.515249` | `11.823088` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `22` | `0.947729` | `-3.0` | `0.363636` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `10` | `-1.007826` | `-3.0` | `0.2` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `3` | `24.247258` | `11.343612` | `1.0` |
| `below_entry_recovery_observation` | `1` | `3.100139` | `15.500693` | `1.0` |
| `pullback_retest_observation` | `22` | `0.947729` | `-3.0` | `0.363636` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `10` | `-1.007826` | `-3.0` | `0.2` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `6` | `-1.918651` | `-3.0` |
| `position_tag` | `BOTTOM` | `6` | `-1.019191` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
