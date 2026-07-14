# Swing Strategy Discovery EV - 2026-07-14

- generated_at: `2026-07-14T20:35:44`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2135` / `13842` / `13842`
- labeled_sample_count: `2550`
- pending_future_quote_count: `4645`
- bottom_rebound_policy_exit_row_count: `2442`
- bottom_rebound_label_status_counts: `{'labeled': 530, 'expired_entry_no_trigger': 686, 'pending_future_quotes': 1226}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 2929, 'PENDING_ENTRY': 1716, 'EXITED': 2550, 'EXPIRED': 6647}, 'label_status_counts': {'pending_future_quotes': 4645, 'expired_entry_no_trigger': 6647, 'labeled': 2550}, 'bottom_rebound_label_status_counts': {'labeled': 530, 'expired_entry_no_trigger': 686, 'pending_future_quotes': 1226}, 'bottom_rebound_maturity_status_counts': {'matured_labeled': 530, 'matured_no_entry': 686, 'pending_future_quotes': 1226}, 'bottom_rebound_pending_future_quote_count': 1226, 'bottom_rebound_labeled_sample_count': 530, 'bottom_rebound_expired_entry_count': 686, 'maturity_status_counts': {'pending_future_quotes': 4645, 'matured_no_entry': 6647, 'matured_labeled': 2550}, 'entry_reason_counts': {'missing_next_quote': 1466, 'next_open': 2590, 'gap_fade_condition_not_met': 1224, 'breakout_not_touched': 2194, 'pullback_not_touched': 2874, 'pullback_limit_touched': 1011, 'gap_fade_limit_touched': 71, 'bottom_rebound_signal_close_retest_touched': 524, 'bottom_rebound_atr_pullback_not_touched': 457, 'bottom_rebound_next_open': 672, 'bottom_rebound_signal_close_retest_not_touched': 148, 'breakout_trigger_touched': 396, 'bottom_rebound_atr_pullback_touched': 215}, 'policy_exit_reason_counts': {'missing_next_quote': 1466, 'need_10_quotes': 2583, 'gap_fade_condition_not_met': 1224, 'breakout_not_touched': 2194, 'pullback_not_touched': 2874, 'fixed_5d_close': 1020, 'fixed_10d_close': 905, 'mae_stop_touched': 534, 'scale_in_recovery_10d_close': 6, 'bottom_rebound_atr_pullback_not_touched': 457, 'bottom_rebound_signal_close_retest_not_touched': 148, 'trailing_after_mfe_10d_close': 7, 'trailing_after_mfe_stop': 77, 'need_5_quotes': 346, 'mae_stop_time_stop_10d_close': 1}, 'source_quality_status_counts': {'pending_future_quotes': 4645, 'ok': 9197}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `84` | `14.235159` | `2.103318` | `0.916667` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 20, 'total_row_count': 96, 'entry_fill_rate': 0.208333, 'expired_rate': 0.520833, 'equal_weight_avg_final_return_pct': -8.633927, 'notional_weighted_ev_pct': -9.200651, 'source_quality_adjusted_ev_pct': -9.200651, 'diagnostic_win_rate': 0.15, 'downside_p10_pct': -25.868831, 'mae_p90_pct': -32.231766}`
- discovery_combined: `{'sample_count': 2530, 'source_quality_adjusted_ev_pct': -5.765265}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1299` | `-3.588429` | `-18.25905` | `0.313318` |
| `wick_stop_recovered_close_above_stop` | `619` | `-6.458173` | `-20.615385` | `0.189015` |
| `close_below_stop` | `632` | `-9.164006` | `-25.428983` | `0.109177` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `104` | `16.812272` | `-9.352544` | `0.413462` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `318` | `-1.11276` | `-12.595616` | `0.402516` |
| `below_entry_recovery_observation` | `504` | `-5.922059` | `-19.374144` | `0.301587` |
| `premium_entry_continuation_observation` | `10` | `-6.020997` | `-14.746442` | `0.3` |
| `pullback_retest_observation` | `619` | `-6.458173` | `-20.615385` | `0.189015` |
| `neutral_location_observation` | `363` | `-8.118617` | `-19.824858` | `0.22314` |
| `invalidation_observation` | `632` | `-9.164006` | `-25.428983` | `0.109177` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `13` | `-19.089682` | `-29.735386` |
| `theme_tags` | `반도체_후공정장비` | `16` | `-18.514207` | `-32.659978` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `15` | `-17.934217` | `-42.151642` |
| `sector` | `Computer programming, System Integration and Management Services` | `25` | `-17.572814` | `-28.521201` |
| `sector` | `Manufacture of Man-Made Fibers` | `14` | `-17.249168` | `-27.256091` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `9` | `-16.859286` | `-24.144648` |
| `theme_tags` | `원자력_설계시공` | `10` | `-15.601597` | `-28.390046` |
| `theme_tags` | `태양광_폴리실리콘` | `9` | `-15.442711` | `-32.421052` |
| `sector` | `Manufacture of Semiconductor` | `55` | `-15.195825` | `-29.374605` |
| `theme_tags` | `합성섬유_원료,합성수지` | `5` | `-15.140046` | `-21.437423` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `8` | `-15.071632` | `-19.668508` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `15` | `-14.947409` | `-34.021464` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `57` | `-14.663612` | `-27.59504` |
| `theme_tags` | `SI(시스템통합)` | `9` | `-14.382251` | `-21.835443` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `29` | `-13.856645` | `-19.479581` |
| `theme_tags` | `희소금속` | `15` | `-13.714797` | `-24.156242` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `18` | `-13.664864` | `-24.095929` |
| `sector` | `Building of Ships and Boats` | `29` | `-13.353891` | `-28.853792` |
| `theme_tags` | `비철금속주` | `12` | `-13.037444` | `-18.274954` |
| `theme_tags` | `방위산업,조선_Eco선` | `12` | `-12.904157` | `-24.90381` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
