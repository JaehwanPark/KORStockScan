# Swing Strategy Discovery EV - 2026-07-07

- generated_at: `2026-07-07T20:23:46`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1709` / `11136` / `11136`
- labeled_sample_count: `1820`
- pending_future_quote_count: `3973`
- bottom_rebound_policy_exit_row_count: `1880`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1007, 'expired_entry_no_trigger': 581, 'labeled': 292}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 5343, 'ENTERED': 2969, 'PENDING_ENTRY': 1004, 'EXITED': 1820}, 'label_status_counts': {'pending_future_quotes': 3973, 'expired_entry_no_trigger': 5343, 'labeled': 1820}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1007, 'expired_entry_no_trigger': 581, 'labeled': 292}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1007, 'matured_no_entry': 581, 'matured_labeled': 292}, 'bottom_rebound_pending_future_quote_count': 1007, 'bottom_rebound_labeled_sample_count': 292, 'bottom_rebound_expired_entry_count': 581, 'maturity_status_counts': {'pending_future_quotes': 3973, 'matured_no_entry': 5343, 'matured_labeled': 1820}, 'entry_reason_counts': {'next_open': 2262, 'pullback_not_touched': 2358, 'breakout_not_touched': 1856, 'gap_fade_condition_not_met': 1064, 'pullback_limit_touched': 1035, 'breakout_trigger_touched': 406, 'gap_fade_limit_touched': 67, 'bottom_rebound_signal_close_retest_touched': 354, 'bottom_rebound_atr_pullback_not_touched': 359, 'bottom_rebound_next_open': 512, 'bottom_rebound_signal_close_retest_not_touched': 158, 'bottom_rebound_atr_pullback_touched': 153, 'missing_next_quote': 552}, 'policy_exit_reason_counts': {'need_5_quotes': 369, 'pullback_not_touched': 2358, 'breakout_not_touched': 1856, 'gap_fade_condition_not_met': 1064, 'need_10_quotes': 2600, 'fixed_5d_close': 829, 'fixed_10d_close': 415, 'trailing_after_mfe_stop': 92, 'mae_stop_touched': 478, 'scale_in_recovery_10d_close': 4, 'trailing_after_mfe_10d_close': 1, 'bottom_rebound_atr_pullback_not_touched': 359, 'bottom_rebound_signal_close_retest_not_touched': 158, 'mae_stop_time_stop_10d_close': 1, 'missing_next_quote': 552}, 'source_quality_status_counts': {'pending_future_quotes': 3973, 'ok': 7163}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `93` | `16.728021` | `2.367296` | `0.989247` |
| `arm08_breakout_risk_mae_time` | `162` | `0.533183` | `-3.0` | `0.006173` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 17, 'total_row_count': 72, 'entry_fill_rate': 0.236111, 'expired_rate': 0.486111, 'equal_weight_avg_final_return_pct': -5.94467, 'notional_weighted_ev_pct': -6.14324, 'source_quality_adjusted_ev_pct': -6.14324, 'diagnostic_win_rate': 0.235294, 'downside_p10_pct': -19.081499, 'mae_p90_pct': -24.234849}`
- discovery_combined: `{'sample_count': 1803, 'source_quality_adjusted_ev_pct': -3.577838}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `829` | `-1.029863` | `-16.212523` | `0.361882` |
| `wick_stop_recovered_close_above_stop` | `536` | `-3.078519` | `-15.626309` | `0.244403` |
| `close_below_stop` | `455` | `-8.775941` | `-21.803499` | `0.134066` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `83` | `20.513946` | `-12.325083` | `0.457831` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `254` | `-1.532394` | `-16.592987` | `0.42126` |
| `below_entry_recovery_observation` | `286` | `-2.51474` | `-14.807302` | `0.342657` |
| `pullback_retest_observation` | `536` | `-3.078519` | `-15.626309` | `0.244403` |
| `premium_entry_continuation_observation` | `2` | `-6.193525` | `-19.517751` | `0.0` |
| `neutral_location_observation` | `204` | `-6.84079` | `-19.338868` | `0.279412` |
| `invalidation_observation` | `455` | `-8.775941` | `-21.803499` | `0.134066` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Television Broadcasting` | `6` | `-18.143337` | `-25.139286` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `7` | `-16.826542` | `-23.752495` |
| `theme_tags` | `비철금속주` | `6` | `-15.904186` | `-19.299611` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `10` | `-15.709778` | `-32.292672` |
| `sector` | `Manufacture of Plastics and Synethetic Rubber in Primary forms` | `7` | `-15.497408` | `-14.867337` |
| `theme_tags` | `원자력_설계시공` | `6` | `-15.475008` | `-22.671185` |
| `sector` | `Manufacture of Man-Made Fibers` | `7` | `-15.401456` | `-20.920502` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `5` | `-14.824366` | `-23.192126` |
| `theme_tags` | `SI(시스템통합)` | `5` | `-14.488617` | `-20.141962` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `11` | `-14.405703` | `-19.755102` |
| `theme_tags` | `로봇_지능형` | `5` | `-14.240565` | `-14.887526` |
| `theme_tags` | `미디어_디지털방송전환` | `8` | `-14.202349` | `-24.447174` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `23` | `-13.589932` | `-22.60008` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `8` | `-12.801077` | `-26.112565` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `9` | `-12.264794` | `-27.389974` |
| `sector` | `Computer programming, System Integration and Management Services` | `22` | `-12.107059` | `-20.909091` |
| `sector` | `Manufacture of Semiconductor` | `40` | `-12.057285` | `-23.988502` |
| `theme_tags` | `반도체_후공정장비` | `11` | `-11.979756` | `-20.955316` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `16` | `-11.716748` | `-26.765799` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `10` | `-10.412186` | `-22.383253` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
