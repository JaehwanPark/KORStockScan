# Swing Strategy Discovery EV - 2026-07-27

- generated_at: `2026-07-27T23:50:40`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `3092` / `20761` / `20761`
- labeled_sample_count: `4041`
- pending_future_quote_count: `6277`
- bottom_rebound_policy_exit_row_count: `3857`
- bottom_rebound_label_status_counts: `{'expired_entry_no_trigger': 1333, 'pending_future_quotes': 1656, 'labeled': 868}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 10443, 'PENDING_ENTRY': 1356, 'EXITED': 4041, 'ENTERED': 4921}, 'label_status_counts': {'expired_entry_no_trigger': 10443, 'pending_future_quotes': 6277, 'labeled': 4041}, 'bottom_rebound_label_status_counts': {'expired_entry_no_trigger': 1333, 'pending_future_quotes': 1656, 'labeled': 868}, 'bottom_rebound_maturity_status_counts': {'matured_no_entry': 1333, 'pending_future_quotes': 1656, 'matured_labeled': 868}, 'bottom_rebound_pending_future_quote_count': 1656, 'bottom_rebound_labeled_sample_count': 868, 'bottom_rebound_expired_entry_count': 1333, 'maturity_status_counts': {'matured_no_entry': 10443, 'pending_future_quotes': 6277, 'matured_labeled': 4041}, 'entry_reason_counts': {'pullback_not_touched': 5070, 'breakout_not_touched': 3348, 'missing_next_quote': 200, 'next_open': 4406, 'gap_fade_condition_not_met': 2113, 'bottom_rebound_signal_close_retest_touched': 705, 'breakout_trigger_touched': 1058, 'bottom_rebound_signal_close_retest_not_touched': 274, 'bottom_rebound_atr_pullback_not_touched': 794, 'bottom_rebound_next_open': 979, 'gap_fade_limit_touched': 90, 'bottom_rebound_atr_pullback_touched': 185, 'pullback_limit_touched': 1539}, 'policy_exit_reason_counts': {'pullback_not_touched': 5070, 'breakout_not_touched': 3348, 'missing_next_quote': 200, 'fixed_5d_close': 1418, 'gap_fade_condition_not_met': 2113, 'need_10_quotes': 4046, 'need_5_quotes': 875, 'fixed_10d_close': 1648, 'bottom_rebound_signal_close_retest_not_touched': 274, 'bottom_rebound_atr_pullback_not_touched': 794, 'trailing_after_mfe_stop': 239, 'mae_stop_time_stop_10d_close': 5, 'mae_stop_touched': 704, 'scale_in_recovery_10d_close': 25, 'scale_in_not_triggered_10d_close': 2}, 'source_quality_status_counts': {'ok': 14484, 'pending_future_quotes': 6277}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `239` | `8.598684` | `2.312002` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 21, 'total_row_count': 96, 'entry_fill_rate': 0.21875, 'expired_rate': 0.739583, 'equal_weight_avg_final_return_pct': -8.141458, 'notional_weighted_ev_pct': -8.561509, 'source_quality_adjusted_ev_pct': -8.561509, 'diagnostic_win_rate': 0.285714, 'downside_p10_pct': -23.394056, 'mae_p90_pct': -27.272727}`
- discovery_combined: `{'sample_count': 4020, 'source_quality_adjusted_ev_pct': -5.85989}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1814` | `-3.06167` | `-18.447144` | `0.385336` |
| `wick_stop_recovered_close_above_stop` | `1229` | `-4.720448` | `-19.271177` | `0.239219` |
| `close_below_stop` | `998` | `-11.693793` | `-28.143035` | `0.127255` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `discount_entry_observation` | `11` | `18.475281` | `-3.0` | `0.272727` |
| `momentum_chase_observation` | `115` | `17.777461` | `-3.0` | `0.678261` |
| `premium_entry_continuation_observation` | `3` | `0.691787` | `-1.983406` | `0.666667` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `below_entry_recovery_observation` | `608` | `-3.690682` | `-18.712117` | `0.402961` |
| `pullback_retest_observation` | `1229` | `-4.720448` | `-19.271177` | `0.239219` |
| `neutral_location_observation` | `1077` | `-5.032125` | `-18.893678` | `0.344475` |
| `invalidation_observation` | `998` | `-11.693793` | `-28.143035` | `0.127255` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Precious Metals and Ornamentations` | `6` | `-43.675777` | `-44.630247` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `15` | `-24.64888` | `-49.857427` |
| `theme_tags` | `휴대폰_수동부품` | `10` | `-19.567287` | `-22.912273` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `22` | `-19.328824` | `-39.353932` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `18` | `-18.051521` | `-30.039871` |
| `theme_tags` | `기계_건설기계` | `22` | `-17.793112` | `-26.598478` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `8` | `-17.474691` | `-34.382567` |
| `theme_tags` | `2차전지_소재(양극화물질등),태양광_발전/설치/운영,태양광_잉곳/웨이퍼/셀/모듈,태양광_폴리실리콘,합성수지` | `5` | `-17.414831` | `-22.128897` |
| `theme_tags` | `LED,PCB(인쇄회로기판),스마트폰_애플 관련주,휴대폰_카메라` | `6` | `-17.024821` | `-26.781858` |
| `sector` | `Other Specialized Wholesale` | `33` | `-16.834606` | `-32.450251` |
| `sector` | `Transit and Ground Passenger Transportation` | `6` | `-16.483708` | `-24.798924` |
| `theme_tags` | `SI(시스템통합)` | `14` | `-15.432498` | `-22.182538` |
| `theme_tags` | `희소금속` | `15` | `-15.305369` | `-25.756798` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `12` | `-14.770699` | `-23.752495` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `18` | `-14.555739` | `-28.593629` |
| `sector` | `Computer programming, System Integration and Management Services` | `39` | `-14.34391` | `-22.777702` |
| `theme_tags` | `로봇_지능형` | `7` | `-14.240565` | `-19.67748` |
| `theme_tags` | `자동차_전장화 수혜` | `14` | `-13.575251` | `-25.462069` |
| `theme_tags` | `반도체_후공정장비` | `24` | `-13.292696` | `-35.709417` |
| `theme_tags` | `2차전지_완제품,그린카_하이브리드카/전기차,합성고무,합성수지` | `9` | `-12.846037` | `-24.195804` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
