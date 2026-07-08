# Swing Strategy Discovery EV - 2026-07-08

- generated_at: `2026-07-08T20:23:30`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1770` / `11456` / `11456`
- labeled_sample_count: `1921`
- pending_future_quote_count: `3809`
- bottom_rebound_policy_exit_row_count: `2032`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1066, 'labeled': 367, 'expired_entry_no_trigger': 599}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 5726, 'EXITED': 1921, 'ENTERED': 2872, 'PENDING_ENTRY': 937}, 'label_status_counts': {'pending_future_quotes': 3809, 'expired_entry_no_trigger': 5726, 'labeled': 1921}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1066, 'labeled': 367, 'expired_entry_no_trigger': 599}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1066, 'matured_labeled': 367, 'matured_no_entry': 599}, 'bottom_rebound_pending_future_quote_count': 1066, 'bottom_rebound_labeled_sample_count': 367, 'bottom_rebound_expired_entry_count': 599, 'maturity_status_counts': {'pending_future_quotes': 3809, 'matured_no_entry': 5726, 'matured_labeled': 1921}, 'entry_reason_counts': {'breakout_not_touched': 1960, 'pullback_not_touched': 2568, 'pullback_limit_touched': 912, 'gap_fade_condition_not_met': 1099, 'next_open': 2320, 'breakout_trigger_touched': 360, 'gap_fade_limit_touched': 61, 'missing_next_quote': 520, 'bottom_rebound_signal_close_retest_touched': 441, 'bottom_rebound_atr_pullback_not_touched': 405, 'bottom_rebound_next_open': 552, 'bottom_rebound_signal_close_retest_not_touched': 111, 'bottom_rebound_atr_pullback_touched': 147}, 'policy_exit_reason_counts': {'breakout_not_touched': 1960, 'pullback_not_touched': 2568, 'need_10_quotes': 2504, 'gap_fade_condition_not_met': 1099, 'fixed_5d_close': 853, 'fixed_10d_close': 541, 'trailing_after_mfe_stop': 92, 'mae_stop_touched': 428, 'scale_in_recovery_10d_close': 5, 'missing_next_quote': 520, 'bottom_rebound_atr_pullback_not_touched': 405, 'bottom_rebound_signal_close_retest_not_touched': 111, 'need_5_quotes': 368, 'mae_stop_time_stop_10d_close': 1, 'trailing_after_mfe_10d_close': 1}, 'source_quality_status_counts': {'pending_future_quotes': 3809, 'ok': 7647}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `93` | `17.504189` | `2.402315` | `0.989247` |
| `arm08_breakout_risk_mae_time` | `130` | `0.972207` | `-3.0` | `0.007692` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 15, 'total_row_count': 80, 'entry_fill_rate': 0.1875, 'expired_rate': 0.5, 'equal_weight_avg_final_return_pct': -11.077325, 'notional_weighted_ev_pct': -11.391368, 'source_quality_adjusted_ev_pct': -11.391368, 'diagnostic_win_rate': 0.133333, 'downside_p10_pct': -29.827214, 'mae_p90_pct': -35.543231}`
- discovery_combined: `{'sample_count': 1906, 'source_quality_adjusted_ev_pct': -3.653679}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `895` | `-0.327247` | `-14.642079` | `0.377654` |
| `wick_stop_recovered_close_above_stop` | `574` | `-4.61067` | `-15.77366` | `0.198606` |
| `close_below_stop` | `452` | `-8.531955` | `-24.262481` | `0.130531` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `91` | `22.798082` | `-7.591093` | `0.549451` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `225` | `-0.001625` | `-10.542636` | `0.413333` |
| `below_entry_recovery_observation` | `359` | `-3.06148` | `-15.175719` | `0.381616` |
| `pullback_retest_observation` | `574` | `-4.61067` | `-15.77366` | `0.198606` |
| `premium_entry_continuation_observation` | `5` | `-5.4104` | `-11.195444` | `0.2` |
| `neutral_location_observation` | `215` | `-5.669633` | `-16.51096` | `0.265116` |
| `invalidation_observation` | `452` | `-8.531955` | `-24.262481` | `0.130531` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `11` | `-19.030039` | `-29.374605` |
| `theme_tags` | `반도체_후공정장비` | `12` | `-16.849353` | `-26.652939` |
| `sector` | `Computer programming, System Integration and Management Services` | `25` | `-16.464789` | `-28.521201` |
| `theme_tags` | `비철금속주` | `8` | `-15.941493` | `-18.365127` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `10` | `-15.523702` | `-33.850742` |
| `sector` | `Manufacture of Semiconductor` | `41` | `-15.118244` | `-29.374605` |
| `sector` | `Manufacture of Man-Made Fibers` | `10` | `-14.335675` | `-18.783069` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `24` | `-14.053065` | `-19.433962` |
| `theme_tags` | `태양광_폴리실리콘` | `7` | `-14.031121` | `-28.898598` |
| `theme_tags` | `그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체` | `10` | `-14.015132` | `-22.451171` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `7` | `-13.808577` | `-19.9801` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `14` | `-13.215965` | `-22.302961` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `6` | `-13.180743` | `-17.829457` |
| `theme_tags` | `미디어_디지털방송전환` | `6` | `-13.156684` | `-25.544933` |
| `sector` | `Manufacture of Gas, Distribution of Gaseous Fuel Through Mains` | `5` | `-13.125846` | `-8.833254` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `10` | `-12.26422` | `-24.660167` |
| `sector` | `Manufacture of Plastics and Synethetic Rubber in Primary forms` | `7` | `-11.711712` | `-11.711712` |
| `theme_tags` | `원자력_설계시공` | `5` | `-11.217108` | `-15.033012` |
| `theme_tags` | `2차전지_완제품,그린카_하이브리드카/전기차,합성고무,합성수지` | `8` | `-11.206742` | `-16.345547` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `12` | `-11.165839` | `-24.599398` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
