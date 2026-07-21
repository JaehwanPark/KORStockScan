# Swing Strategy Discovery EV - 2026-07-21

- generated_at: `2026-07-21T20:41:37`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2621` / `17313` / `17313`
- labeled_sample_count: `3386`
- pending_future_quote_count: `5885`
- bottom_rebound_policy_exit_row_count: `3153`
- bottom_rebound_label_status_counts: `{'labeled': 918, 'expired_entry_no_trigger': 935, 'pending_future_quotes': 1300}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXITED': 3386, 'EXPIRED': 8042, 'ENTERED': 3535, 'PENDING_ENTRY': 2350}, 'label_status_counts': {'labeled': 3386, 'pending_future_quotes': 5885, 'expired_entry_no_trigger': 8042}, 'bottom_rebound_label_status_counts': {'labeled': 918, 'expired_entry_no_trigger': 935, 'pending_future_quotes': 1300}, 'bottom_rebound_maturity_status_counts': {'matured_labeled': 918, 'matured_no_entry': 935, 'pending_future_quotes': 1300}, 'bottom_rebound_pending_future_quote_count': 1300, 'bottom_rebound_labeled_sample_count': 918, 'bottom_rebound_expired_entry_count': 935, 'maturity_status_counts': {'matured_labeled': 3386, 'pending_future_quotes': 5885, 'matured_no_entry': 8042}, 'entry_reason_counts': {'next_open': 3308, 'missing_next_quote': 1612, 'pullback_not_touched': 3498, 'breakout_not_touched': 2958, 'gap_fade_condition_not_met': 1575, 'bottom_rebound_next_open': 823, 'bottom_rebound_atr_pullback_not_touched': 584, 'breakout_trigger_touched': 350, 'bottom_rebound_signal_close_retest_touched': 658, 'pullback_limit_touched': 1464, 'bottom_rebound_signal_close_retest_not_touched': 165, 'gap_fade_limit_touched': 79, 'bottom_rebound_atr_pullback_touched': 239}, 'policy_exit_reason_counts': {'fixed_10d_close': 1484, 'missing_next_quote': 1612, 'fixed_5d_close': 1200, 'pullback_not_touched': 3498, 'breakout_not_touched': 2958, 'gap_fade_condition_not_met': 1575, 'bottom_rebound_atr_pullback_not_touched': 584, 'trailing_after_mfe_10d_close': 4, 'need_10_quotes': 3002, 'bottom_rebound_signal_close_retest_not_touched': 165, 'trailing_after_mfe_stop': 61, 'mae_stop_touched': 618, 'scale_in_recovery_10d_close': 18, 'need_5_quotes': 533, 'mae_stop_time_stop_10d_close': 1}, 'source_quality_status_counts': {'ok': 11428, 'pending_future_quotes': 5885}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `65` | `17.072726` | `2.091948` | `0.938462` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 21, 'total_row_count': 96, 'entry_fill_rate': 0.21875, 'expired_rate': 0.625, 'equal_weight_avg_final_return_pct': -13.47369, 'notional_weighted_ev_pct': -14.160691, 'source_quality_adjusted_ev_pct': -14.160691, 'diagnostic_win_rate': 0.095238, 'downside_p10_pct': -33.155792, 'mae_p90_pct': -38.340249}`
- discovery_combined: `{'sample_count': 3365, 'source_quality_adjusted_ev_pct': -7.041944}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1550` | `-3.869808` | `-17.782946` | `0.311613` |
| `wick_stop_recovered_close_above_stop` | `828` | `-6.903861` | `-21.248404` | `0.201691` |
| `close_below_stop` | `1008` | `-11.634062` | `-28.060889` | `0.111111` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `118` | `13.708347` | `-11.285139` | `0.322034` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `354` | `-1.601756` | `-13.149021` | `0.378531` |
| `premium_entry_continuation_observation` | `10` | `-5.352005` | `-14.746442` | `0.3` |
| `below_entry_recovery_observation` | `583` | `-5.502257` | `-19.272087` | `0.319039` |
| `pullback_retest_observation` | `828` | `-6.903861` | `-21.248404` | `0.201691` |
| `neutral_location_observation` | `485` | `-7.634316` | `-19.030631` | `0.251546` |
| `invalidation_observation` | `1008` | `-11.634062` | `-28.060889` | `0.111111` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Precious Metals and Ornamentations` | `6` | `-45.015279` | `-47.487015` |
| `theme_tags` | `기계_건설기계` | `17` | `-25.089354` | `-34.847423` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `19` | `-21.641411` | `-44.57915` |
| `theme_tags` | `휴대폰_수동부품` | `8` | `-21.603145` | `-31.431597` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `16` | `-20.289795` | `-29.881145` |
| `sector` | `Transit and Ground Passenger Transportation` | `5` | `-19.992809` | `-25.897356` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `19` | `-18.913774` | `-40.325366` |
| `sector` | `Manufacture of Man-Made Fibers` | `15` | `-18.804401` | `-27.038104` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `11` | `-18.267311` | `-23.920052` |
| `sector` | `Other Specialized Wholesale` | `32` | `-17.199359` | `-30.925328` |
| `sector` | `Computer programming, System Integration and Management Services` | `35` | `-17.14408` | `-27.897633` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `53` | `-16.567588` | `-19.616439` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `45` | `-16.084012` | `-32.447257` |
| `theme_tags` | `반도체_후공정장비` | `22` | `-15.970198` | `-28.435073` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `18` | `-15.86744` | `-40.479361` |
| `theme_tags` | `원자력_설계시공` | `12` | `-15.711692` | `-28.058279` |
| `theme_tags` | `SI(시스템통합),스마트 그리드` | `16` | `-15.515768` | `-27.121212` |
| `theme_tags` | `방위산업,조선_Eco선` | `14` | `-15.359312` | `-29.51431` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `8` | `-15.295123` | `-34.691296` |
| `theme_tags` | `그린카_하이브리드카/전기차` | `33` | `-15.244357` | `-25.41649` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
