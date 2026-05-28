# Swing Strategy Discovery EV - 2026-05-28

- generated_at: `2026-05-28T16:32:45`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `375` / `2854` / `2854`
- labeled_sample_count: `82`
- pending_future_quote_count: `2557`
- bottom_rebound_policy_exit_row_count: `126`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 126}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `1`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1849, 'ENTERED': 708, 'EXITED': 82, 'EXPIRED': 215}, 'label_status_counts': {'pending_future_quotes': 2557, 'labeled': 82, 'expired_entry_no_trigger': 215}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 126}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 126}, 'bottom_rebound_pending_future_quote_count': 126, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'pending_future_quotes': 2557, 'matured_labeled': 82, 'matured_no_entry': 215}, 'entry_reason_counts': {'next_open': 468, 'pullback_not_touched': 507, 'breakout_trigger_touched': 108, 'gap_fade_condition_not_met': 215, 'breakout_not_touched': 360, 'pullback_limit_touched': 195, 'gap_fade_limit_touched': 19, 'missing_next_quote': 982}, 'policy_exit_reason_counts': {'need_5_quotes': 253, 'need_10_quotes': 455, 'pullback_not_touched': 507, 'trailing_after_mfe_stop': 30, 'gap_fade_condition_not_met': 215, 'breakout_not_touched': 360, 'mae_stop_touched': 52, 'missing_next_quote': 982}, 'source_quality_status_counts': {'pending_future_quotes': 2557, 'ok': 297}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `30` | `12.458811` | `5.367158` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 82, 'source_quality_adjusted_ev_pct': 2.38796}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `19` | `14.386414` | `7.090461` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `40` | `0.813244` | `-3.0` | `0.25` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `23` | `-2.472758` | `-3.0` | `0.043478` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `below_entry_recovery_observation` | `4` | `13.857144` | `11.007728` | `1.0` |
| `momentum_chase_observation` | `15` | `13.183423` | `6.968306` | `1.0` |
| `pullback_retest_observation` | `40` | `0.813244` | `-3.0` | `0.25` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `23` | `-2.472758` | `-3.0` | `0.043478` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Other Financial Intermediation` | `6` | `-1.26811` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
