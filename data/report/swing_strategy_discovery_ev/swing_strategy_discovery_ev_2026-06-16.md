# Swing Strategy Discovery EV - 2026-06-16

- generated_at: `2026-06-16T16:15:44`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `768` / `4929` / `4929`
- labeled_sample_count: `429`
- pending_future_quote_count: `3698`
- bottom_rebound_policy_exit_row_count: `857`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 747, 'expired_entry_no_trigger': 91, 'labeled': 19}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `8`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 2070, 'PENDING_ENTRY': 1628, 'EXPIRED': 802, 'EXITED': 429}, 'label_status_counts': {'pending_future_quotes': 3698, 'expired_entry_no_trigger': 802, 'labeled': 429}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 747, 'expired_entry_no_trigger': 91, 'labeled': 19}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 747, 'matured_no_entry': 91, 'matured_labeled': 19}, 'bottom_rebound_pending_future_quote_count': 747, 'bottom_rebound_labeled_sample_count': 19, 'bottom_rebound_expired_entry_count': 91, 'maturity_status_counts': {'pending_future_quotes': 3698, 'matured_no_entry': 802, 'matured_labeled': 429}, 'entry_reason_counts': {'next_open': 802, 'pullback_limit_touched': 615, 'bottom_rebound_atr_pullback_not_touched': 156, 'breakout_not_touched': 222, 'gap_fade_condition_not_met': 367, 'bottom_rebound_next_open': 234, 'bottom_rebound_signal_close_retest_not_touched': 78, 'gap_fade_limit_touched': 34, 'pullback_not_touched': 588, 'breakout_trigger_touched': 580, 'missing_next_quote': 1019, 'bottom_rebound_signal_close_retest_touched': 156, 'bottom_rebound_atr_pullback_touched': 78}, 'policy_exit_reason_counts': {'need_10_quotes': 1635, 'bottom_rebound_atr_pullback_not_touched': 156, 'breakout_not_touched': 222, 'gap_fade_condition_not_met': 367, 'bottom_rebound_signal_close_retest_not_touched': 78, 'need_5_quotes': 435, 'pullback_not_touched': 588, 'mae_stop_touched': 250, 'trailing_after_mfe_stop': 179, 'missing_next_quote': 1019}, 'source_quality_status_counts': {'pending_future_quotes': 3698, 'ok': 1231}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `179` | `8.992258` | `2.323651` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 3, 'total_row_count': 24, 'entry_fill_rate': 0.125, 'expired_rate': 0.375, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.8, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -16.415217}`
- discovery_combined: `{'sample_count': 426, 'source_quality_adjusted_ev_pct': 2.76621}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `152` | `7.731171` | `-3.0` | `0.815789` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `204` | `-0.075386` | `-3.0` | `0.210784` |
| `close_below_stop` | `73` | `-0.703494` | `-3.0` | `0.164384` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `103` | `9.431204` | `2.703449` | `0.961165` |
| `below_entry_recovery_observation` | `38` | `3.569647` | `-3.0` | `0.473684` |
| `neutral_location_observation` | `5` | `3.404794` | `-3.0` | `0.6` |
| `premium_entry_continuation_observation` | `4` | `2.27842` | `2.16096` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `204` | `-0.075386` | `-3.0` | `0.210784` |
| `invalidation_observation` | `73` | `-0.703494` | `-3.0` | `0.164384` |
| `discount_entry_observation` | `2` | `-1.2` | `-3.0` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Software Development and Supply` | `9` | `-3.0` | `-3.0` |
| `theme_tags` | `반도체_생산` | `8` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `14` | `-2.231381` | `-3.0` |
| `sector` | `-` | `6` | `-1.960558` | `-3.0` |
| `sector` | `Computer programming, System Integration and Management Services` | `8` | `-1.813285` | `-3.0` |
| `block_reason` | `blocked_swing_gap` | `9` | `-1.761762` | `-3.0` |
| `theme_tags` | `PCB(인쇄회로기판)` | `9` | `-0.980996` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `7` | `-0.872628` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
