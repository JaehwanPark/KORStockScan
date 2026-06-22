# Swing Strategy Discovery EV - 2026-06-22

- generated_at: `2026-06-22T16:02:46`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1133` / `7197` / `7197`
- labeled_sample_count: `917`
- pending_future_quote_count: `4315`
- bottom_rebound_policy_exit_row_count: `1325`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 941, 'labeled': 121, 'expired_entry_no_trigger': 263}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1357, 'ENTERED': 2958, 'EXPIRED': 1965, 'EXITED': 917}, 'label_status_counts': {'pending_future_quotes': 4315, 'expired_entry_no_trigger': 1965, 'labeled': 917}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 941, 'labeled': 121, 'expired_entry_no_trigger': 263}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 941, 'matured_labeled': 121, 'matured_no_entry': 263}, 'bottom_rebound_pending_future_quote_count': 941, 'bottom_rebound_labeled_sample_count': 121, 'bottom_rebound_expired_entry_count': 263, 'maturity_status_counts': {'pending_future_quotes': 4315, 'matured_no_entry': 1965, 'matured_labeled': 917}, 'entry_reason_counts': {'missing_next_quote': 937, 'bottom_rebound_signal_close_retest_touched': 308, 'bottom_rebound_next_open': 364, 'next_open': 1292, 'pullback_limit_touched': 1185, 'breakout_not_touched': 812, 'pullback_not_touched': 753, 'breakout_trigger_touched': 480, 'gap_fade_condition_not_met': 591, 'gap_fade_limit_touched': 55, 'bottom_rebound_atr_pullback_not_touched': 173, 'bottom_rebound_atr_pullback_touched': 191, 'bottom_rebound_signal_close_retest_not_touched': 56}, 'policy_exit_reason_counts': {'missing_next_quote': 937, 'need_10_quotes': 2441, 'breakout_not_touched': 812, 'pullback_not_touched': 753, 'trailing_after_mfe_stop': 134, 'gap_fade_condition_not_met': 591, 'mae_stop_touched': 599, 'fixed_5d_close': 184, 'bottom_rebound_atr_pullback_not_touched': 173, 'bottom_rebound_signal_close_retest_not_touched': 56, 'need_5_quotes': 517}, 'source_quality_status_counts': {'pending_future_quotes': 4315, 'ok': 2882}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `134` | `7.735478` | `2.609122` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 8, 'total_row_count': 64, 'entry_fill_rate': 0.125, 'expired_rate': 0.171875, 'equal_weight_avg_final_return_pct': -4.717131, 'notional_weighted_ev_pct': -5.437856, 'source_quality_adjusted_ev_pct': -5.437856, 'diagnostic_win_rate': 0.125, 'downside_p10_pct': -11.697343, 'mae_p90_pct': -20.280341}`
- discovery_combined: `{'sample_count': 909, 'source_quality_adjusted_ev_pct': 0.813369}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `238` | `3.938549` | `-3.0` | `0.558824` |
| `wick_stop_recovered_close_above_stop` | `421` | `0.263983` | `-3.0` | `0.220903` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `258` | `-2.078541` | `-3.0` | `0.096899` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `55` | `6.031886` | `-3.0` | `0.545455` |
| `discount_entry_observation` | `42` | `4.574089` | `-3.0` | `0.595238` |
| `neutral_location_observation` | `44` | `3.881825` | `-3.0` | `0.545455` |
| `below_entry_recovery_observation` | `92` | `2.388371` | `-3.0` | `0.565217` |
| `premium_entry_continuation_observation` | `5` | `1.018194` | `-3.0` | `0.4` |
| `pullback_retest_observation` | `421` | `0.263983` | `-3.0` | `0.220903` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `258` | `-2.078541` | `-3.0` | `0.096899` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Computer programming, System Integration and Management Services` | `16` | `-7.848164` | `-21.356554` |
| `theme_tags` | `비철금속주` | `5` | `-5.952853` | `-7.60553` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `6` | `-5.000785` | `-8.842806` |
| `sector` | `Retail Sale of Fuel` | `5` | `-4.726428` | `-7.520393` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `12` | `-4.654012` | `-10.792518` |
| `theme_tags` | `클라우드 컴퓨팅` | `5` | `-4.512402` | `-6.903839` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `12` | `-4.339402` | `-3.0` |
| `sector` | `Telecommunications` | `6` | `-4.248349` | `-6.2532` |
| `theme_tags` | `기계_건설기계` | `5` | `-3.89412` | `-5.607004` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `26` | `-3.529866` | `-12.97541` |
| `theme_tags` | `그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체` | `8` | `-3.113047` | `-5.362712` |
| `sector` | `Road Freight Transport` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Man-Made Fibers` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Other Transport Equipment` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `8` | `-3.0` | `-3.0` |
| `theme_tags` | `의복_아웃도어` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `화장품` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `SI(시스템통합)` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `자원개발 E&P` | `14` | `-2.742873` | `-4.566008` |
| `theme_tags` | `SI(시스템통합),스마트 그리드` | `6` | `-2.625962` | `-6.223127` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
