# Swing Strategy Discovery EV - 2026-06-19

- generated_at: `2026-06-19T16:46:58`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1047` / `6660` / `6660`
- labeled_sample_count: `535`
- pending_future_quote_count: `4128`
- bottom_rebound_policy_exit_row_count: `1196`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 853, 'expired_entry_no_trigger': 322, 'labeled': 21}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `16`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1711, 'ENTERED': 2417, 'EXPIRED': 1997, 'EXITED': 535}, 'label_status_counts': {'pending_future_quotes': 4128, 'expired_entry_no_trigger': 1997, 'labeled': 535}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 853, 'expired_entry_no_trigger': 322, 'labeled': 21}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 853, 'matured_no_entry': 322, 'matured_labeled': 21}, 'bottom_rebound_pending_future_quote_count': 853, 'bottom_rebound_labeled_sample_count': 21, 'bottom_rebound_expired_entry_count': 322, 'maturity_status_counts': {'pending_future_quotes': 4128, 'matured_no_entry': 1997, 'matured_labeled': 535}, 'entry_reason_counts': {'breakout_not_touched': 706, 'bottom_rebound_signal_close_retest_touched': 211, 'bottom_rebound_signal_close_retest_not_touched': 118, 'next_open': 1174, 'missing_next_quote': 977, 'bottom_rebound_atr_pullback_touched': 98, 'bottom_rebound_next_open': 329, 'bottom_rebound_atr_pullback_not_touched': 231, 'breakout_trigger_touched': 468, 'pullback_not_touched': 1134, 'gap_fade_condition_not_met': 542, 'pullback_limit_touched': 627, 'gap_fade_limit_touched': 45}, 'policy_exit_reason_counts': {'breakout_not_touched': 706, 'need_10_quotes': 1911, 'bottom_rebound_signal_close_retest_not_touched': 118, 'need_5_quotes': 506, 'missing_next_quote': 977, 'bottom_rebound_atr_pullback_not_touched': 231, 'fixed_5d_close': 126, 'pullback_not_touched': 1134, 'gap_fade_condition_not_met': 542, 'mae_stop_touched': 268, 'trailing_after_mfe_stop': 141}, 'source_quality_status_counts': {'pending_future_quotes': 4128, 'ok': 2532}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `141` | `8.66295` | `2.465048` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 5, 'total_row_count': 40, 'entry_fill_rate': 0.125, 'expired_rate': 0.3, 'equal_weight_avg_final_return_pct': -1.778869, 'notional_weighted_ev_pct': -1.729219, 'source_quality_adjusted_ev_pct': -1.729219, 'diagnostic_win_rate': 0.4, 'downside_p10_pct': -6.654545, 'mae_p90_pct': -8.744089}`
- discovery_combined: `{'sample_count': 530, 'source_quality_adjusted_ev_pct': 3.733352}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `190` | `7.700046` | `-3.0` | `0.694737` |
| `wick_stop_recovered_close_above_stop` | `174` | `2.26126` | `-3.0` | `0.321839` |
| `close_below_stop` | `171` | `0.444426` | `-3.0` | `0.280702` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `neutral_location_observation` | `74` | `8.887178` | `-3.0` | `0.702703` |
| `momentum_chase_observation` | `66` | `8.561138` | `-3.0` | `0.772727` |
| `below_entry_recovery_observation` | `40` | `5.520988` | `-3.0` | `0.625` |
| `pullback_retest_observation` | `174` | `2.26126` | `-3.0` | `0.321839` |
| `premium_entry_continuation_observation` | `8` | `0.615052` | `-3.0` | `0.5` |
| `invalidation_observation` | `171` | `0.444426` | `-3.0` | `0.280702` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `2` | `-1.2` | `-3.0` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Computer programming, System Integration and Management Services` | `8` | `-4.107131` | `-9.090909` |
| `theme_tags` | `그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체` | `5` | `-1.915975` | `-3.0` |
| `sector` | `Manufacture of primary battery and secondary battery` | `6` | `-1.885112` | `-3.0` |
| `theme_tags` | `의복_아웃도어` | `6` | `-1.782424` | `-3.0` |
| `theme_tags` | `증권,창투` | `7` | `-1.191037` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `15` | `-1.037075` | `-3.0` |
| `sector` | `Manufacture of Plastic Products` | `5` | `-0.823188` | `-3.0` |
| `sector` | `Activities Auxiliary to Financial Service Activities` | `8` | `-0.736383` | `-3.0` |
| `theme_tags` | `증권` | `8` | `-0.736383` | `-3.0` |
| `theme_tags` | `운송_해운` | `10` | `-0.490353` | `-3.304454` |
| `sector` | `Sea and Coastal Water Transport` | `12` | `-0.490353` | `-3.0` |
| `theme_tags` | `자원개발 E&P` | `8` | `-0.365137` | `-3.0` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `13` | `-0.302174` | `-3.0` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `7` | `-0.185396` | `-3.0` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `10` | `0.602561` | `-10.392157` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `34` | `0.701284` | `-7.398694` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
