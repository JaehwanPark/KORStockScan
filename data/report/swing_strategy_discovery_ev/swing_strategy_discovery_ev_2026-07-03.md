# Swing Strategy Discovery EV - 2026-07-03

- generated_at: `2026-07-03T20:23:48`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1578` / `10416` / `10416`
- labeled_sample_count: `1546`
- pending_future_quote_count: `4079`
- bottom_rebound_policy_exit_row_count: `1568`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 801, 'expired_entry_no_trigger': 545, 'labeled': 222}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXITED': 1546, 'EXPIRED': 4791, 'ENTERED': 2893, 'PENDING_ENTRY': 1186}, 'label_status_counts': {'labeled': 1546, 'expired_entry_no_trigger': 4791, 'pending_future_quotes': 4079}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 801, 'expired_entry_no_trigger': 545, 'labeled': 222}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 801, 'matured_no_entry': 545, 'matured_labeled': 222}, 'bottom_rebound_pending_future_quote_count': 801, 'bottom_rebound_labeled_sample_count': 222, 'bottom_rebound_expired_entry_count': 545, 'maturity_status_counts': {'matured_labeled': 1546, 'matured_no_entry': 4791, 'pending_future_quotes': 4079}, 'entry_reason_counts': {'breakout_trigger_touched': 342, 'gap_fade_condition_not_met': 974, 'pullback_not_touched': 2019, 'bottom_rebound_next_open': 433, 'breakout_not_touched': 1738, 'bottom_rebound_atr_pullback_not_touched': 312, 'bottom_rebound_signal_close_retest_not_touched': 137, 'next_open': 2080, 'pullback_limit_touched': 1101, 'gap_fade_limit_touched': 66, 'bottom_rebound_signal_close_retest_touched': 296, 'bottom_rebound_atr_pullback_touched': 121, 'missing_next_quote': 797}, 'policy_exit_reason_counts': {'trailing_after_mfe_stop': 105, 'gap_fade_condition_not_met': 974, 'pullback_not_touched': 2019, 'mae_stop_touched': 477, 'need_10_quotes': 2508, 'breakout_not_touched': 1738, 'bottom_rebound_atr_pullback_not_touched': 312, 'bottom_rebound_signal_close_retest_not_touched': 137, 'fixed_5d_close': 721, 'fixed_10d_close': 242, 'scale_in_recovery_10d_close': 1, 'need_5_quotes': 385, 'missing_next_quote': 797}, 'source_quality_status_counts': {'ok': 6337, 'pending_future_quotes': 4079}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `105` | `16.539719` | `2.468405` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 17, 'total_row_count': 72, 'entry_fill_rate': 0.236111, 'expired_rate': 0.472222, 'equal_weight_avg_final_return_pct': -5.853824, 'notional_weighted_ev_pct': -6.04367, 'source_quality_adjusted_ev_pct': -6.04367, 'diagnostic_win_rate': 0.235294, 'downside_p10_pct': -19.081499, 'mae_p90_pct': -24.234849}`
- discovery_combined: `{'sample_count': 1529, 'source_quality_adjusted_ev_pct': -3.902466}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `697` | `-2.043573` | `-17.768012` | `0.319943` |
| `wick_stop_recovered_close_above_stop` | `425` | `-2.616637` | `-14.844598` | `0.251765` |
| `close_below_stop` | `424` | `-8.427576` | `-21.765172` | `0.143868` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `67` | `17.006493` | `-12.311781` | `0.492537` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `237` | `-1.974728` | `-17.255956` | `0.35865` |
| `premium_entry_continuation_observation` | `9` | `-2.473558` | `-12.802052` | `0.444444` |
| `pullback_retest_observation` | `425` | `-2.616637` | `-14.844598` | `0.251765` |
| `below_entry_recovery_observation` | `212` | `-4.023332` | `-15.270449` | `0.268868` |
| `neutral_location_observation` | `172` | `-7.538103` | `-19.732254` | `0.255814` |
| `invalidation_observation` | `424` | `-8.427576` | `-21.765172` | `0.143868` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Other Transport Equipment` | `6` | `-23.167421` | `-13.083711` |
| `theme_tags` | `원자력_설계시공` | `5` | `-18.167283` | `-22.898853` |
| `sector` | `Manufacture of Man-Made Fibers` | `5` | `-18.014963` | `-20.920502` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `6` | `-16.055756` | `-23.752495` |
| `sector` | `Manufacture of Plastics and Synethetic Rubber in Primary forms` | `6` | `-15.497408` | `-15.497408` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `9` | `-14.457321` | `-32.556873` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `5` | `-14.404904` | `-23.643094` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `8` | `-12.824413` | `-27.630886` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `11` | `-12.81892` | `-19.343066` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `9` | `-12.607816` | `-22.383253` |
| `theme_tags` | `SI(시스템통합)` | `6` | `-12.579628` | `-19.506721` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `20` | `-11.575487` | `-23.62732` |
| `theme_tags` | `증권,창투` | `5` | `-11.39686` | `-18.484629` |
| `sector` | `Computer programming, System Integration and Management Services` | `21` | `-11.081912` | `-20.909091` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `19` | `-10.515187` | `-26.765799` |
| `sector` | `Manufacture of Semiconductor` | `36` | `-10.485835` | `-23.626247` |
| `theme_tags` | `미디어_디지털방송전환` | `6` | `-10.337791` | `-18.0` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `29` | `-9.994077` | `-27.021682` |
| `theme_tags` | `그린카_하이브리드카/전기차` | `21` | `-9.991782` | `-22.383253` |
| `sector` | `Telecommunications` | `7` | `-9.642133` | `-14.901594` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
