# Swing Strategy Discovery EV - 2026-07-24

- generated_at: `2026-07-24T20:40:26`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `3003` / `20177` / `20177`
- labeled_sample_count: `3659`
- pending_future_quote_count: `7052`
- bottom_rebound_policy_exit_row_count: `3729`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1681, 'expired_entry_no_trigger': 1182, 'labeled': 866}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 4337, 'EXPIRED': 9466, 'PENDING_ENTRY': 2715, 'EXITED': 3659}, 'label_status_counts': {'pending_future_quotes': 7052, 'expired_entry_no_trigger': 9466, 'labeled': 3659}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1681, 'expired_entry_no_trigger': 1182, 'labeled': 866}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1681, 'matured_no_entry': 1182, 'matured_labeled': 866}, 'bottom_rebound_pending_future_quote_count': 1681, 'bottom_rebound_labeled_sample_count': 866, 'bottom_rebound_expired_entry_count': 1182, 'maturity_status_counts': {'pending_future_quotes': 7052, 'matured_no_entry': 9466, 'matured_labeled': 3659}, 'entry_reason_counts': {'bottom_rebound_signal_close_retest_touched': 660, 'bottom_rebound_atr_pullback_not_touched': 706, 'missing_next_quote': 1603, 'next_open': 3958, 'bottom_rebound_next_open': 914, 'bottom_rebound_atr_pullback_touched': 208, 'pullback_not_touched': 4593, 'breakout_trigger_touched': 840, 'gap_fade_condition_not_met': 1907, 'bottom_rebound_signal_close_retest_not_touched': 254, 'breakout_not_touched': 3118, 'gap_fade_limit_touched': 72, 'pullback_limit_touched': 1344}, 'policy_exit_reason_counts': {'need_10_quotes': 3558, 'bottom_rebound_atr_pullback_not_touched': 706, 'missing_next_quote': 1603, 'pullback_not_touched': 4593, 'gap_fade_condition_not_met': 1907, 'bottom_rebound_signal_close_retest_not_touched': 254, 'breakout_not_touched': 3118, 'need_5_quotes': 779, 'fixed_5d_close': 1272, 'fixed_10d_close': 1584, 'trailing_after_mfe_stop': 201, 'mae_stop_time_stop_10d_close': 7, 'trailing_after_mfe_10d_close': 1, 'mae_stop_touched': 565, 'scale_in_recovery_10d_close': 27, 'scale_in_not_triggered_10d_close': 2}, 'source_quality_status_counts': {'pending_future_quotes': 7052, 'ok': 13125}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `202` | `9.800166` | `2.432009` | `0.99505` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 21, 'total_row_count': 96, 'entry_fill_rate': 0.21875, 'expired_rate': 0.739583, 'equal_weight_avg_final_return_pct': -8.127183, 'notional_weighted_ev_pct': -8.550425, 'source_quality_adjusted_ev_pct': -8.550425, 'diagnostic_win_rate': 0.333333, 'downside_p10_pct': -23.394056, 'mae_p90_pct': -27.272727}`
- discovery_combined: `{'sample_count': 3638, 'source_quality_adjusted_ev_pct': -6.046921}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1771` | `-3.123749` | `-18.677686` | `0.381141` |
| `wick_stop_recovered_close_above_stop` | `1060` | `-5.24481` | `-20.224452` | `0.212264` |
| `close_below_stop` | `828` | `-12.540603` | `-28.616939` | `0.131643` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `201` | `7.01254` | `-12.133891` | `0.512438` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `premium_entry_continuation_observation` | `19` | `-0.694386` | `-14.132566` | `0.473684` |
| `below_entry_recovery_observation` | `582` | `-3.295721` | `-19.633623` | `0.410653` |
| `discount_entry_observation` | `434` | `-3.367538` | `-18.677686` | `0.40553` |
| `pullback_retest_observation` | `1060` | `-5.24481` | `-20.224452` | `0.212264` |
| `neutral_location_observation` | `535` | `-7.295787` | `-19.236333` | `0.276636` |
| `invalidation_observation` | `828` | `-12.540603` | `-28.616939` | `0.131643` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Precious Metals and Ornamentations` | `6` | `-43.732348` | `-44.686151` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `13` | `-25.655818` | `-50.765012` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `19` | `-21.326435` | `-39.748304` |
| `theme_tags` | `휴대폰_수동부품` | `10` | `-19.986342` | `-23.970005` |
| `sector` | `Transit and Ground Passenger Transportation` | `5` | `-19.241987` | `-24.916902` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `16` | `-18.891056` | `-30.451068` |
| `sector` | `Other Specialized Wholesale` | `30` | `-17.816975` | `-32.828283` |
| `theme_tags` | `기계_건설기계` | `21` | `-17.793112` | `-27.321429` |
| `theme_tags` | `SI(시스템통합)` | `13` | `-17.551221` | `-22.349334` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `8` | `-17.436557` | `-34.382567` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `10` | `-16.859985` | `-24.444444` |
| `sector` | `Computer programming, System Integration and Management Services` | `33` | `-16.050639` | `-23.062027` |
| `theme_tags` | `반도체_후공정장비` | `22` | `-14.42337` | `-35.940119` |
| `theme_tags` | `로봇_지능형` | `7` | `-14.240565` | `-19.67748` |
| `theme_tags` | `희소금속` | `17` | `-13.855245` | `-25.756798` |
| `theme_tags` | `자동차_전장화 수혜` | `14` | `-13.575251` | `-25.462069` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `23` | `-13.495405` | `-19.672695` |
| `theme_tags` | `바이오_줄기세포치료제` | `17` | `-13.264396` | `-20.89449` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `14` | `-13.240672` | `-23.752495` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `47` | `-13.219261` | `-29.964851` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
