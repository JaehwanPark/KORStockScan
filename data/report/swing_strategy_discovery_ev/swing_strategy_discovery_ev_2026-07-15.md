# Swing Strategy Discovery EV - 2026-07-15

- generated_at: `2026-07-15T20:32:09`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2229` / `14482` / `14482`
- labeled_sample_count: `2686`
- pending_future_quote_count: `4601`
- bottom_rebound_policy_exit_row_count: `2650`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1253, 'labeled': 595, 'expired_entry_no_trigger': 802}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 7195, 'EXITED': 2686, 'ENTERED': 2937, 'PENDING_ENTRY': 1664}, 'label_status_counts': {'labeled': 2686, 'expired_entry_no_trigger': 7195, 'pending_future_quotes': 4601}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1253, 'labeled': 595, 'expired_entry_no_trigger': 802}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1253, 'matured_labeled': 595, 'matured_no_entry': 802}, 'bottom_rebound_pending_future_quote_count': 1253, 'bottom_rebound_labeled_sample_count': 595, 'bottom_rebound_expired_entry_count': 802, 'maturity_status_counts': {'matured_labeled': 2686, 'matured_no_entry': 7195, 'pending_future_quotes': 4601}, 'entry_reason_counts': {'next_open': 2768, 'pullback_not_touched': 3075, 'bottom_rebound_atr_pullback_not_touched': 465, 'gap_fade_condition_not_met': 1320, 'bottom_rebound_signal_close_retest_touched': 527, 'bottom_rebound_next_open': 710, 'missing_next_quote': 1280, 'breakout_not_touched': 2536, 'bottom_rebound_atr_pullback_touched': 245, 'bottom_rebound_signal_close_retest_not_touched': 183, 'breakout_trigger_touched': 232, 'gap_fade_limit_touched': 64, 'pullback_limit_touched': 1077}, 'policy_exit_reason_counts': {'fixed_10d_close': 990, 'pullback_not_touched': 3075, 'bottom_rebound_atr_pullback_not_touched': 465, 'gap_fade_condition_not_met': 1320, 'need_5_quotes': 371, 'need_10_quotes': 2566, 'missing_next_quote': 1280, 'breakout_not_touched': 2536, 'mae_stop_touched': 558, 'fixed_5d_close': 1077, 'bottom_rebound_signal_close_retest_not_touched': 183, 'trailing_after_mfe_stop': 55, 'trailing_after_mfe_10d_close': 4, 'mae_stop_time_stop_10d_close': 1, 'scale_in_recovery_10d_close': 1}, 'source_quality_status_counts': {'ok': 9881, 'pending_future_quotes': 4601}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `59` | `19.100605` | `2.469389` | `0.932203` |
| `arm08_breakout_risk_mae_time` | `107` | `1.808868` | `-3.0` | `0.009346` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 18, 'total_row_count': 96, 'entry_fill_rate': 0.1875, 'expired_rate': 0.552083, 'equal_weight_avg_final_return_pct': -5.792199, 'notional_weighted_ev_pct': -6.08784, 'source_quality_adjusted_ev_pct': -6.08784, 'diagnostic_win_rate': 0.222222, 'downside_p10_pct': -18.776901, 'mae_p90_pct': -23.935736}`
- discovery_combined: `{'sample_count': 2668, 'source_quality_adjusted_ev_pct': -6.491006}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1241` | `-3.648004` | `-19.343066` | `0.302981` |
| `wick_stop_recovered_close_above_stop` | `640` | `-5.83554` | `-20.565735` | `0.209375` |
| `close_below_stop` | `805` | `-10.98377` | `-27.034483` | `0.115528` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `93` | `14.290122` | `-18.74902` | `0.311828` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `359` | `-2.881468` | `-18.164108` | `0.367688` |
| `below_entry_recovery_observation` | `380` | `-4.88878` | `-19.655892` | `0.315789` |
| `pullback_retest_observation` | `640` | `-5.83554` | `-20.565735` | `0.209375` |
| `neutral_location_observation` | `397` | `-7.392828` | `-19.530661` | `0.234257` |
| `premium_entry_continuation_observation` | `12` | `-7.816563` | `-15.557332` | `0.166667` |
| `invalidation_observation` | `805` | `-10.98377` | `-27.034483` | `0.115528` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `15` | `-22.858961` | `-49.857427` |
| `theme_tags` | `반도체_후공정장비` | `14` | `-20.201484` | `-36.05547` |
| `sector` | `Television Broadcasting` | `7` | `-18.806324` | `-16.226087` |
| `sector` | `Manufacture of Man-Made Fibers` | `10` | `-18.720026` | `-22.402172` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `5` | `-18.40825` | `-20.649404` |
| `theme_tags` | `SI(시스템통합)` | `9` | `-18.229789` | `-23.264018` |
| `theme_tags` | `원자력_설계시공` | `11` | `-16.783231` | `-23.809524` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `12` | `-16.475856` | `-28.073511` |
| `theme_tags` | `희소금속` | `15` | `-16.249148` | `-25.756798` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `13` | `-15.764938` | `-23.752495` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `14` | `-15.432417` | `-32.0` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `54` | `-15.266758` | `-35.991041` |
| `sector` | `Other Specialized Wholesale` | `23` | `-15.142871` | `-32.828283` |
| `sector` | `Computer programming, System Integration and Management Services` | `25` | `-15.132838` | `-22.967252` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `16` | `-14.656871` | `-21.367747` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `13` | `-14.641841` | `-34.74506` |
| `sector` | `Building of Ships and Boats` | `33` | `-14.348045` | `-25.843956` |
| `theme_tags` | `로봇_지능형` | `5` | `-14.240565` | `-19.700268` |
| `sector` | `Manufacture of primary battery and secondary battery` | `64` | `-14.154825` | `-25.756798` |
| `theme_tags` | `2차전지_완제품,그린카_하이브리드카/전기차,합성고무,합성수지` | `10` | `-14.058394` | `-23.636364` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
