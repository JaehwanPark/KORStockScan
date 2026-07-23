# Swing Strategy Discovery EV - 2026-07-23

- generated_at: `2026-07-23T20:34:24`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2876` / `19214` / `19214`
- labeled_sample_count: `3385`
- pending_future_quote_count: `6665`
- bottom_rebound_policy_exit_row_count: `3518`
- bottom_rebound_label_status_counts: `{'expired_entry_no_trigger': 1127, 'pending_future_quotes': 1557, 'labeled': 834}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXITED': 3385, 'EXPIRED': 9164, 'ENTERED': 3964, 'PENDING_ENTRY': 2701}, 'label_status_counts': {'labeled': 3385, 'expired_entry_no_trigger': 9164, 'pending_future_quotes': 6665}, 'bottom_rebound_label_status_counts': {'expired_entry_no_trigger': 1127, 'pending_future_quotes': 1557, 'labeled': 834}, 'bottom_rebound_maturity_status_counts': {'matured_no_entry': 1127, 'pending_future_quotes': 1557, 'matured_labeled': 834}, 'bottom_rebound_pending_future_quote_count': 1557, 'bottom_rebound_labeled_sample_count': 834, 'bottom_rebound_expired_entry_count': 1127, 'maturity_status_counts': {'matured_labeled': 3385, 'matured_no_entry': 9164, 'pending_future_quotes': 6665}, 'entry_reason_counts': {'next_open': 3746, 'pullback_not_touched': 4419, 'bottom_rebound_atr_pullback_not_touched': 724, 'breakout_trigger_touched': 616, 'bottom_rebound_signal_close_retest_touched': 663, 'gap_fade_condition_not_met': 1787, 'breakout_not_touched': 3130, 'pullback_limit_touched': 1200, 'gap_fade_limit_touched': 86, 'bottom_rebound_signal_close_retest_not_touched': 218, 'bottom_rebound_next_open': 881, 'bottom_rebound_atr_pullback_touched': 157, 'missing_next_quote': 1587}, 'policy_exit_reason_counts': {'fixed_5d_close': 1249, 'pullback_not_touched': 4419, 'bottom_rebound_atr_pullback_not_touched': 724, 'need_10_quotes': 3254, 'need_5_quotes': 710, 'gap_fade_condition_not_met': 1787, 'fixed_10d_close': 1540, 'breakout_not_touched': 3130, 'mae_stop_touched': 462, 'scale_in_recovery_10d_close': 16, 'bottom_rebound_signal_close_retest_not_touched': 218, 'trailing_after_mfe_10d_close': 1, 'trailing_after_mfe_stop': 116, 'mae_stop_time_stop_10d_close': 1, 'missing_next_quote': 1587}, 'source_quality_status_counts': {'ok': 12549, 'pending_future_quotes': 6665}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `117` | `11.551208` | `2.429155` | `0.991453` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 20, 'total_row_count': 96, 'entry_fill_rate': 0.208333, 'expired_rate': 0.645833, 'equal_weight_avg_final_return_pct': -14.364732, 'notional_weighted_ev_pct': -14.84983, 'source_quality_adjusted_ev_pct': -14.84983, 'diagnostic_win_rate': 0.1, 'downside_p10_pct': -33.516561, 'mae_p90_pct': -38.401031}`
- discovery_combined: `{'sample_count': 3365, 'source_quality_adjusted_ev_pct': -6.998645}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1573` | `-3.831284` | `-18.309466` | `0.3452` |
| `wick_stop_recovered_close_above_stop` | `803` | `-6.860745` | `-21.293455` | `0.215442` |
| `close_below_stop` | `1009` | `-11.646686` | `-27.98665` | `0.125867` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `132` | `11.26738` | `-13.871213` | `0.507576` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `343` | `-1.469455` | `-13.470728` | `0.402332` |
| `premium_entry_continuation_observation` | `18` | `-2.626419` | `-12.938834` | `0.555556` |
| `below_entry_recovery_observation` | `570` | `-5.602049` | `-19.760244` | `0.335088` |
| `pullback_retest_observation` | `803` | `-6.860745` | `-21.293455` | `0.215442` |
| `neutral_location_observation` | `510` | `-7.448072` | `-19.171271` | `0.268627` |
| `invalidation_observation` | `1009` | `-11.646686` | `-27.98665` | `0.125867` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Precious Metals and Ornamentations` | `6` | `-44.90562` | `-47.38097` |
| `theme_tags` | `기계_건설기계` | `20` | `-25.089354` | `-34.304943` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `20` | `-24.993661` | `-44.266404` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `17` | `-21.632232` | `-33.101706` |
| `theme_tags` | `휴대폰_수동부품` | `8` | `-20.031269` | `-28.345714` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `6` | `-19.897882` | `-35.938485` |
| `sector` | `Transit and Ground Passenger Transportation` | `5` | `-19.871207` | `-25.778354` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `49` | `-18.454542` | `-28.265641` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `10` | `-18.288317` | `-24.359097` |
| `sector` | `Manufacture of Man-Made Fibers` | `18` | `-18.126504` | `-26.384143` |
| `sector` | `Other Specialized Wholesale` | `33` | `-17.440152` | `-30.743301` |
| `sector` | `Computer programming, System Integration and Management Services` | `34` | `-17.408008` | `-28.660655` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `24` | `-17.301538` | `-41.206083` |
| `theme_tags` | `방위산업,조선_Eco선` | `15` | `-16.870869` | `-30.398932` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `44` | `-16.598262` | `-32.447257` |
| `sector` | `Television Broadcasting` | `6` | `-16.521911` | `-28.944977` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `17` | `-16.078022` | `-36.08522` |
| `theme_tags` | `반도체_후공정장비` | `24` | `-16.052828` | `-28.268919` |
| `theme_tags` | `SI(시스템통합),스마트 그리드` | `16` | `-15.525632` | `-27.121212` |
| `sector` | `Heavy Construction` | `32` | `-15.392666` | `-29.298187` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
