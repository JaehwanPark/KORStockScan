# Swing Strategy Discovery EV - 2026-05-29

- generated_at: `2026-05-29T21:27:50`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `486` / `3636` / `3636`
- labeled_sample_count: `225`
- pending_future_quote_count: `2729`
- bottom_rebound_policy_exit_row_count: `292`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 260, 'expired_entry_no_trigger': 10, 'labeled': 22}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `15`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1209, 'ENTERED': 1520, 'EXPIRED': 682, 'EXITED': 225}, 'label_status_counts': {'pending_future_quotes': 2729, 'expired_entry_no_trigger': 682, 'labeled': 225}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 260, 'expired_entry_no_trigger': 10, 'labeled': 22}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 260, 'matured_no_entry': 10, 'matured_labeled': 22}, 'bottom_rebound_pending_future_quote_count': 260, 'bottom_rebound_labeled_sample_count': 22, 'bottom_rebound_expired_entry_count': 10, 'maturity_status_counts': {'pending_future_quotes': 2729, 'matured_no_entry': 682, 'matured_labeled': 225}, 'entry_reason_counts': {'next_open': 750, 'pullback_not_touched': 567, 'breakout_not_touched': 536, 'gap_fade_condition_not_met': 334, 'pullback_limit_touched': 558, 'breakout_trigger_touched': 214, 'gap_fade_limit_touched': 41, 'missing_next_quote': 432, 'bottom_rebound_next_open': 68, 'bottom_rebound_signal_close_retest_touched': 63, 'bottom_rebound_atr_pullback_touched': 51, 'bottom_rebound_atr_pullback_not_touched': 17, 'bottom_rebound_signal_close_retest_not_touched': 5}, 'policy_exit_reason_counts': {'need_10_quotes': 1104, 'pullback_not_touched': 567, 'breakout_not_touched': 536, 'gap_fade_condition_not_met': 334, 'need_5_quotes': 416, 'trailing_after_mfe_stop': 55, 'mae_stop_touched': 170, 'missing_next_quote': 432, 'bottom_rebound_atr_pullback_not_touched': 17, 'bottom_rebound_signal_close_retest_not_touched': 5}, 'source_quality_status_counts': {'pending_future_quotes': 2729, 'ok': 907}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `55` | `9.746865` | `2.66326` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 7, 'total_row_count': 24, 'entry_fill_rate': 0.291667, 'expired_rate': 0.0, 'equal_weight_avg_final_return_pct': -1.81112, 'notional_weighted_ev_pct': -1.541663, 'source_quality_adjusted_ev_pct': -1.541663, 'diagnostic_win_rate': 0.142857, 'downside_p10_pct': -3.0, 'mae_p90_pct': -8.318096}`
- discovery_combined: `{'sample_count': 218, 'source_quality_adjusted_ev_pct': 0.721342}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `22` | `14.029738` | `3.303152` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `118` | `-0.200461` | `-3.0` | `0.220339` |
| `close_below_stop` | `85` | `-2.211534` | `-3.0` | `0.082353` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `16` | `16.463158` | `4.870122` | `1.0` |
| `below_entry_recovery_observation` | `5` | `6.524056` | `2.957421` | `1.0` |
| `neutral_location_observation` | `1` | `2.552157` | `12.760784` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `premium_entry_continuation_observation` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `118` | `-0.200461` | `-3.0` | `0.220339` |
| `invalidation_observation` | `85` | `-2.211534` | `-3.0` | `0.082353` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Sea and Coastal Water Transport` | `8` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `7` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Electric Lamps and Bulbs` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `운송_해운` | `7` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `10` | `-1.795858` | `-3.0` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `5` | `-1.0332` | `-3.0` |
| `position_tag` | `BOTTOM` | `55` | `-0.975969` | `-3.0` |
| `position_tag` | `MIDDLE` | `71` | `-0.777896` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `10` | `-0.656759` | `-3.0` |
| `sector` | `Insurance` | `9` | `-0.571312` | `-3.0` |
| `theme_tags` | `반도체_생산` | `6` | `-0.439346` | `-3.0` |
| `block_reason` | `blocked_swing_gap` | `9` | `-0.021207` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
