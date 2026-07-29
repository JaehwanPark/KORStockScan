# Swing Strategy Discovery EV - 2026-07-28

- generated_at: `2026-07-29T07:34:38`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `3172` / `21401` / `21401`
- labeled_sample_count: `4428`
- pending_future_quote_count: `5980`
- bottom_rebound_policy_exit_row_count: `3857`
- bottom_rebound_label_status_counts: `{'expired_entry_no_trigger': 1454, 'pending_future_quotes': 1439, 'labeled': 964}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1227, 'EXPIRED': 10993, 'ENTERED': 4753, 'EXITED': 4428}, 'label_status_counts': {'pending_future_quotes': 5980, 'expired_entry_no_trigger': 10993, 'labeled': 4428}, 'bottom_rebound_label_status_counts': {'expired_entry_no_trigger': 1454, 'pending_future_quotes': 1439, 'labeled': 964}, 'bottom_rebound_maturity_status_counts': {'matured_no_entry': 1454, 'pending_future_quotes': 1439, 'matured_labeled': 964}, 'bottom_rebound_pending_future_quote_count': 1439, 'bottom_rebound_labeled_sample_count': 964, 'bottom_rebound_expired_entry_count': 1454, 'maturity_status_counts': {'pending_future_quotes': 5980, 'matured_no_entry': 10993, 'matured_labeled': 4428}, 'entry_reason_counts': {'missing_next_quote': 640, 'pullback_not_touched': 4845, 'next_open': 4456, 'gap_fade_condition_not_met': 2109, 'bottom_rebound_atr_pullback_not_touched': 801, 'bottom_rebound_signal_close_retest_touched': 746, 'breakout_not_touched': 3592, 'bottom_rebound_next_open': 979, 'bottom_rebound_signal_close_retest_not_touched': 233, 'gap_fade_limit_touched': 119, 'breakout_trigger_touched': 864, 'pullback_limit_touched': 1839, 'bottom_rebound_atr_pullback_touched': 178}, 'policy_exit_reason_counts': {'missing_next_quote': 640, 'pullback_not_touched': 4845, 'need_5_quotes': 823, 'gap_fade_condition_not_met': 2109, 'bottom_rebound_atr_pullback_not_touched': 801, 'fixed_5d_close': 1524, 'need_10_quotes': 3930, 'breakout_not_touched': 3592, 'fixed_10d_close': 1701, 'bottom_rebound_signal_close_retest_not_touched': 233, 'trailing_after_mfe_stop': 180, 'mae_stop_touched': 1000, 'mae_stop_time_stop_10d_close': 1, 'scale_in_recovery_10d_close': 20, 'trailing_after_mfe_10d_close': 2}, 'source_quality_status_counts': {'pending_future_quotes': 5980, 'ok': 15421}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `182` | `9.889135` | `2.380443` | `0.989011` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 22, 'total_row_count': 96, 'entry_fill_rate': 0.229167, 'expired_rate': 0.708333, 'equal_weight_avg_final_return_pct': -13.495651, 'notional_weighted_ev_pct': -14.188121, 'source_quality_adjusted_ev_pct': -14.188121, 'diagnostic_win_rate': 0.090909, 'downside_p10_pct': -32.747905, 'mae_p90_pct': -38.221609}`
- discovery_combined: `{'sample_count': 4406, 'source_quality_adjusted_ev_pct': -6.226767}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `2145` | `-3.388086` | `-16.893289` | `0.318881` |
| `wick_stop_recovered_close_above_stop` | `969` | `-6.852766` | `-21.46433` | `0.209494` |
| `close_below_stop` | `1314` | `-10.346093` | `-26.037095` | `0.106545` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `219` | `5.384921` | `-11.620958` | `0.438356` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `495` | `-1.042585` | `-11.878736` | `0.369697` |
| `premium_entry_continuation_observation` | `39` | `-1.744743` | `-9.852076` | `0.410256` |
| `below_entry_recovery_observation` | `693` | `-5.284659` | `-19.894108` | `0.324675` |
| `neutral_location_observation` | `699` | `-6.123537` | `-17.727399` | `0.234621` |
| `pullback_retest_observation` | `969` | `-6.852766` | `-21.46433` | `0.209494` |
| `invalidation_observation` | `1314` | `-10.346093` | `-26.037095` | `0.106545` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Precious Metals and Ornamentations` | `6` | `-44.740304` | `-47.221104` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `17` | `-27.586792` | `-45.204643` |
| `theme_tags` | `기계_건설기계` | `26` | `-23.182231` | `-32.784126` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `21` | `-22.986887` | `-33.398072` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `20` | `-20.657412` | `-33.888149` |
| `theme_tags` | `휴대폰_수동부품` | `7` | `-18.900912` | `-27.898086` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `7` | `-17.967217` | `-35.314891` |
| `sector` | `Transit and Ground Passenger Transportation` | `6` | `-16.906573` | `-25.515935` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `29` | `-16.758714` | `-39.790247` |
| `sector` | `Other Specialized Wholesale` | `35` | `-16.701515` | `-30.379249` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `13` | `-16.21275` | `-23.728762` |
| `theme_tags` | `반도체_후공정장비` | `25` | `-15.91046` | `-27.482548` |
| `sector` | `Computer programming, System Integration and Management Services` | `42` | `-15.750659` | `-23.226188` |
| `sector` | `Manufacture of Man-Made Fibers` | `21` | `-15.70097` | `-25.730181` |
| `theme_tags` | `희소금속` | `14` | `-15.428934` | `-27.512248` |
| `theme_tags` | `LED,PCB(인쇄회로기판),스마트폰_애플 관련주,휴대폰_카메라` | `7` | `-14.459324` | `-25.070119` |
| `theme_tags` | `그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품` | `9` | `-14.433643` | `-43.773608` |
| `sector` | `Wholesale of Construction Materials, Hardware and Heating and Air Conditioning Equipment` | `7` | `-13.711995` | `-25.500435` |
| `theme_tags` | `자원개발 E&P` | `48` | `-13.263836` | `-25.853373` |
| `theme_tags` | `SI(시스템통합),스마트 그리드` | `17` | `-13.084555` | `-27.121212` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
