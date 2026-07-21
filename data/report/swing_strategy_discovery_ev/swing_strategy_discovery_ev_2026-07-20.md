# Swing Strategy Discovery EV - 2026-07-20

- generated_at: `2026-07-20T20:46:46`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2485` / `16341` / `16341`
- labeled_sample_count: `2919`
- pending_future_quote_count: `5552`
- bottom_rebound_policy_exit_row_count: `3045`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1373, 'labeled': 719, 'expired_entry_no_trigger': 953}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 7870, 'EXITED': 2919, 'ENTERED': 3003, 'PENDING_ENTRY': 2549}, 'label_status_counts': {'expired_entry_no_trigger': 7870, 'pending_future_quotes': 5552, 'labeled': 2919}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1373, 'labeled': 719, 'expired_entry_no_trigger': 953}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1373, 'matured_labeled': 719, 'matured_no_entry': 953}, 'bottom_rebound_pending_future_quote_count': 1373, 'bottom_rebound_labeled_sample_count': 719, 'bottom_rebound_expired_entry_count': 953, 'maturity_status_counts': {'matured_no_entry': 7870, 'pending_future_quotes': 5552, 'matured_labeled': 2919}, 'entry_reason_counts': {'breakout_not_touched': 2834, 'bottom_rebound_next_open': 790, 'missing_next_quote': 1563, 'bottom_rebound_atr_pullback_touched': 186, 'next_open': 3102, 'bottom_rebound_signal_close_retest_touched': 571, 'bottom_rebound_signal_close_retest_not_touched': 219, 'bottom_rebound_atr_pullback_not_touched': 604, 'pullback_not_touched': 3729, 'gap_fade_condition_not_met': 1470, 'gap_fade_limit_touched': 81, 'breakout_trigger_touched': 268, 'pullback_limit_touched': 924}, 'policy_exit_reason_counts': {'breakout_not_touched': 2834, 'need_10_quotes': 2531, 'missing_next_quote': 1563, 'fixed_5d_close': 1160, 'fixed_10d_close': 1282, 'bottom_rebound_signal_close_retest_not_touched': 219, 'bottom_rebound_atr_pullback_not_touched': 604, 'pullback_not_touched': 3729, 'gap_fade_condition_not_met': 1470, 'mae_stop_touched': 416, 'trailing_after_mfe_stop': 53, 'need_5_quotes': 472, 'trailing_after_mfe_10d_close': 4, 'mae_stop_time_stop_10d_close': 1, 'scale_in_recovery_10d_close': 3}, 'source_quality_status_counts': {'ok': 10789, 'pending_future_quotes': 5552}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `57` | `18.310249` | `2.422481` | `0.929825` |
| `arm08_breakout_risk_mae_time` | `102` | `1.723166` | `-3.0` | `0.009804` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 20, 'total_row_count': 96, 'entry_fill_rate': 0.208333, 'expired_rate': 0.635417, 'equal_weight_avg_final_return_pct': -9.08767, 'notional_weighted_ev_pct': -9.43624, 'source_quality_adjusted_ev_pct': -9.43624, 'diagnostic_win_rate': 0.25, 'downside_p10_pct': -23.502203, 'mae_p90_pct': -27.94768}`
- discovery_combined: `{'sample_count': 2899, 'source_quality_adjusted_ev_pct': -7.072798}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1422` | `-4.120828` | `-19.466499` | `0.319972` |
| `wick_stop_recovered_close_above_stop` | `712` | `-6.290515` | `-22.032954` | `0.200843` |
| `close_below_stop` | `785` | `-12.51843` | `-28.460856` | `0.127389` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `44` | `55.7686` | `-5.408673` | `0.409091` |
| `premium_entry_continuation_observation` | `2` | `1.115345` | `2.62258` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `26` | `-3.0` | `-3.0` | `0.0` |
| `below_entry_recovery_observation` | `430` | `-5.056809` | `-20.505263` | `0.323256` |
| `neutral_location_observation` | `920` | `-5.554428` | `-19.589172` | `0.321739` |
| `pullback_retest_observation` | `712` | `-6.290515` | `-22.032954` | `0.200843` |
| `invalidation_observation` | `785` | `-12.51843` | `-28.460856` | `0.127389` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `5` | `-24.484134` | `-34.382567` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `14` | `-24.096492` | `-50.31122` |
| `sector` | `Transit and Ground Passenger Transportation` | `5` | `-19.486908` | `-25.275399` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `11` | `-18.743416` | `-32.0` |
| `sector` | `Manufacture of Man-Made Fibers` | `11` | `-18.720026` | `-22.036262` |
| `theme_tags` | `휴대폰_수동부품` | `8` | `-18.657978` | `-24.362606` |
| `theme_tags` | `원자력_설계시공` | `10` | `-17.920786` | `-24.895238` |
| `sector` | `Other Specialized Wholesale` | `27` | `-17.708187` | `-32.828283` |
| `theme_tags` | `SI(시스템통합)` | `11` | `-17.551221` | `-22.682927` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `15` | `-17.468492` | `-34.149963` |
| `theme_tags` | `2차전지_완제품,그린카_하이브리드카/전기차,태양광_잉곳/웨이퍼/셀/모듈` | `6` | `-17.001953` | `-22.960993` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `9` | `-16.859985` | `-24.444444` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `12` | `-16.475856` | `-28.073511` |
| `theme_tags` | `희소금속` | `15` | `-16.249148` | `-25.756798` |
| `theme_tags` | `반도체_후공정장비` | `16` | `-15.871504` | `-36.05547` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `11` | `-15.715543` | `-23.752495` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `9` | `-15.700003` | `-25.454545` |
| `sector` | `Computer programming, System Integration and Management Services` | `29` | `-15.53919` | `-23.643118` |
| `theme_tags` | `그린카_하이브리드카/전기차` | `26` | `-14.88365` | `-25.994939` |
| `sector` | `Manufacture of primary battery and secondary battery` | `69` | `-14.525173` | `-27.72429` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
