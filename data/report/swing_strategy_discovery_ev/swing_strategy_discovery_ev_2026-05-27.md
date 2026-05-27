# Swing Strategy Discovery EV - 2026-05-27

- generated_at: `2026-05-27T19:06:31`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `284` / `2272` / `2272`
- labeled_sample_count: `84`
- pending_future_quote_count: `2056`
- bottom_rebound_policy_exit_row_count: `0`
- bottom_rebound_label_status_counts: `{}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `2`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1649, 'ENTERED': 407, 'EXITED': 84, 'EXPIRED': 132}, 'label_status_counts': {'pending_future_quotes': 2056, 'labeled': 84, 'expired_entry_no_trigger': 132}, 'bottom_rebound_label_status_counts': {}, 'bottom_rebound_maturity_status_counts': {}, 'bottom_rebound_pending_future_quote_count': 0, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'pending_future_quotes': 2056, 'matured_labeled': 84, 'matured_no_entry': 132}, 'entry_reason_counts': {'next_open': 300, 'pullback_not_touched': 441, 'breakout_trigger_touched': 164, 'gap_fade_condition_not_met': 132, 'breakout_not_touched': 136, 'gap_fade_limit_touched': 18, 'pullback_limit_touched': 9, 'missing_next_quote': 1072}, 'policy_exit_reason_counts': {'need_5_quotes': 168, 'need_10_quotes': 239, 'pullback_not_touched': 441, 'trailing_after_mfe_stop': 46, 'gap_fade_condition_not_met': 132, 'breakout_not_touched': 136, 'mae_stop_touched': 38, 'missing_next_quote': 1072}, 'source_quality_status_counts': {'pending_future_quotes': 2056, 'ok': 216}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `46` | `11.126858` | `2.810699` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 84, 'source_quality_adjusted_ev_pct': 4.804456}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `34` | `12.766939` | `2.880979` | `1.0` |
| `wick_stop_recovered_close_above_stop` | `30` | `0.999899` | `-3.0` | `0.366667` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `20` | `-2.716093` | `-3.0` | `0.05` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `23` | `17.074607` | `6.379634` | `1.0` |
| `below_entry_recovery_observation` | `7` | `4.65017` | `2.664914` | `1.0` |
| `premium_entry_continuation_observation` | `2` | `2.229799` | `4.95766` | `1.0` |
| `neutral_location_observation` | `2` | `1.082817` | `2.576392` | `1.0` |
| `pullback_retest_observation` | `30` | `0.999899` | `-3.0` | `0.366667` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `20` | `-2.716093` | `-3.0` | `0.05` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Real Estate Activities with Own or Leased Property` | `6` | `-0.89516` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `5` | `-0.117214` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
