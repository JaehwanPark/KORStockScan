# Swing Strategy Discovery EV - 2026-07-22

- generated_at: `2026-07-22T20:43:42`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2751` / `18267` / `18267`
- labeled_sample_count: `3424`
- pending_future_quote_count: `6240`
- bottom_rebound_policy_exit_row_count: `3307`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1363, 'expired_entry_no_trigger': 1034, 'labeled': 910}`
- top_surviving_arm: `arm08_breakout_risk_mae_time`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXITED': 3424, 'ENTERED': 3835, 'EXPIRED': 8603, 'PENDING_ENTRY': 2405}, 'label_status_counts': {'labeled': 3424, 'pending_future_quotes': 6240, 'expired_entry_no_trigger': 8603}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1363, 'expired_entry_no_trigger': 1034, 'labeled': 910}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1363, 'matured_no_entry': 1034, 'matured_labeled': 910}, 'bottom_rebound_pending_future_quote_count': 1363, 'bottom_rebound_labeled_sample_count': 910, 'bottom_rebound_expired_entry_count': 1034, 'maturity_status_counts': {'matured_labeled': 3424, 'pending_future_quotes': 6240, 'matured_no_entry': 8603}, 'entry_reason_counts': {'next_open': 3530, 'bottom_rebound_signal_close_retest_touched': 651, 'bottom_rebound_signal_close_retest_not_touched': 200, 'gap_fade_condition_not_met': 1686, 'pullback_not_touched': 3642, 'breakout_trigger_touched': 244, 'bottom_rebound_atr_pullback_not_touched': 600, 'bottom_rebound_atr_pullback_touched': 251, 'breakout_not_touched': 3286, 'bottom_rebound_next_open': 851, 'gap_fade_limit_touched': 79, 'pullback_limit_touched': 1653, 'missing_next_quote': 1594}, 'policy_exit_reason_counts': {'fixed_5d_close': 1224, 'need_10_quotes': 3215, 'bottom_rebound_signal_close_retest_not_touched': 200, 'gap_fade_condition_not_met': 1686, 'pullback_not_touched': 3642, 'bottom_rebound_atr_pullback_not_touched': 600, 'fixed_10d_close': 1510, 'need_5_quotes': 620, 'breakout_not_touched': 3286, 'trailing_after_mfe_stop': 36, 'mae_stop_touched': 636, 'trailing_after_mfe_10d_close': 5, 'mae_stop_time_stop_10d_close': 1, 'scale_in_recovery_10d_close': 12, 'missing_next_quote': 1594}, 'source_quality_status_counts': {'ok': 12027, 'pending_future_quotes': 6240}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm08_breakout_risk_mae_time` | `105` | `1.567607` | `-3.0` | `0.009524` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 19, 'total_row_count': 96, 'entry_fill_rate': 0.197917, 'expired_rate': 0.71875, 'equal_weight_avg_final_return_pct': -9.250179, 'notional_weighted_ev_pct': -9.473813, 'source_quality_adjusted_ev_pct': -9.473813, 'diagnostic_win_rate': 0.263158, 'downside_p10_pct': -23.61035, 'mae_p90_pct': -28.622633}`
- discovery_combined: `{'sample_count': 3405, 'source_quality_adjusted_ev_pct': -7.19963}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1623` | `-4.36964` | `-18.919675` | `0.314233` |
| `wick_stop_recovered_close_above_stop` | `923` | `-6.516431` | `-21.621041` | `0.174431` |
| `close_below_stop` | `878` | `-12.451069` | `-28.485953` | `0.109339` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `124` | `8.513856` | `-18.71759` | `0.298387` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `428` | `-3.818027` | `-18.710744` | `0.376168` |
| `below_entry_recovery_observation` | `526` | `-4.999615` | `-19.655892` | `0.323194` |
| `pullback_retest_observation` | `923` | `-6.516431` | `-21.621041` | `0.174431` |
| `neutral_location_observation` | `533` | `-7.351002` | `-18.919675` | `0.262664` |
| `premium_entry_continuation_observation` | `12` | `-7.816563` | `-15.557332` | `0.166667` |
| `invalidation_observation` | `878` | `-12.451069` | `-28.485953` | `0.109339` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Precious Metals and Ornamentations` | `6` | `-43.845151` | `-44.797623` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `16` | `-25.268009` | `-49.403634` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `19` | `-21.188016` | `-39.748304` |
| `theme_tags` | `휴대폰_수동부품` | `10` | `-20.805687` | `-26.03811` |
| `sector` | `Transit and Ground Passenger Transportation` | `5` | `-19.364692` | `-25.096509` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `7` | `-19.20893` | `-34.382567` |
| `sector` | `Other Specialized Wholesale` | `29` | `-18.095741` | `-32.828283` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `15` | `-18.086245` | `-30.220768` |
| `theme_tags` | `기계_건설기계` | `20` | `-17.793112` | `-28.192681` |
| `sector` | `Manufacture of Man-Made Fibers` | `17` | `-17.697609` | `-23.692308` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `8` | `-17.17016` | `-26.149733` |
| `theme_tags` | `2차전지_완제품,그린카_하이브리드카/전기차,태양광_잉곳/웨이퍼/셀/모듈` | `6` | `-17.001953` | `-22.960993` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `10` | `-16.859985` | `-24.444444` |
| `theme_tags` | `SI(시스템통합)` | `14` | `-16.334088` | `-22.182538` |
| `sector` | `Computer programming, System Integration and Management Services` | `34` | `-15.694355` | `-23.01464` |
| `theme_tags` | `원자력_설계시공` | `14` | `-15.467233` | `-23.126521` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `43` | `-15.449124` | `-29.964851` |
| `theme_tags` | `희소금속` | `16` | `-15.315206` | `-25.756798` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `57` | `-15.308157` | `-26.125` |
| `theme_tags` | `방위산업,조선_Eco선` | `16` | `-14.767657` | `-26.058134` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
