# Swing Strategy Discovery EV - 2026-07-13

- generated_at: `2026-07-13T20:35:55`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1987` / `12808` / `12808`
- labeled_sample_count: `2229`
- pending_future_quote_count: `3963`
- bottom_rebound_policy_exit_row_count: `2288`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1128, 'expired_entry_no_trigger': 722, 'labeled': 438}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 6616, 'PENDING_ENTRY': 1276, 'ENTERED': 2687, 'EXITED': 2229}, 'label_status_counts': {'pending_future_quotes': 3963, 'expired_entry_no_trigger': 6616, 'labeled': 2229}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1128, 'expired_entry_no_trigger': 722, 'labeled': 438}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1128, 'matured_no_entry': 722, 'matured_labeled': 438}, 'bottom_rebound_pending_future_quote_count': 1128, 'bottom_rebound_labeled_sample_count': 438, 'bottom_rebound_expired_entry_count': 722, 'maturity_status_counts': {'pending_future_quotes': 3963, 'matured_no_entry': 6616, 'matured_labeled': 2229}, 'entry_reason_counts': {'pullback_not_touched': 2925, 'bottom_rebound_signal_close_retest_not_touched': 218, 'bottom_rebound_atr_pullback_not_touched': 495, 'bottom_rebound_next_open': 672, 'next_open': 2482, 'breakout_not_touched': 2206, 'gap_fade_condition_not_met': 1184, 'pullback_limit_touched': 798, 'gap_fade_limit_touched': 57, 'breakout_trigger_touched': 276, 'bottom_rebound_signal_close_retest_touched': 454, 'bottom_rebound_atr_pullback_touched': 177, 'missing_next_quote': 864}, 'policy_exit_reason_counts': {'pullback_not_touched': 2925, 'bottom_rebound_signal_close_retest_not_touched': 218, 'bottom_rebound_atr_pullback_not_touched': 495, 'need_10_quotes': 2355, 'need_5_quotes': 332, 'fixed_5d_close': 966, 'fixed_10d_close': 781, 'breakout_not_touched': 2206, 'gap_fade_condition_not_met': 1184, 'mae_stop_touched': 406, 'scale_in_recovery_10d_close': 2, 'trailing_after_mfe_10d_close': 3, 'trailing_after_mfe_stop': 70, 'mae_stop_time_stop_10d_close': 1, 'missing_next_quote': 864}, 'source_quality_status_counts': {'pending_future_quotes': 3963, 'ok': 8845}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `73` | `17.687628` | `2.076241` | `0.958904` |
| `arm08_breakout_risk_mae_time` | `119` | `1.451743` | `-3.0` | `0.008403` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 20, 'total_row_count': 96, 'entry_fill_rate': 0.208333, 'expired_rate': 0.427083, 'equal_weight_avg_final_return_pct': -4.834725, 'notional_weighted_ev_pct': -5.215616, 'source_quality_adjusted_ev_pct': -5.215616, 'diagnostic_win_rate': 0.3, 'downside_p10_pct': -18.167704, 'mae_p90_pct': -23.3681}`
- discovery_combined: `{'sample_count': 2209, 'source_quality_adjusted_ev_pct': -5.498274}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1085` | `-3.287588` | `-19.620254` | `0.322581` |
| `wick_stop_recovered_close_above_stop` | `554` | `-4.999809` | `-20.169306` | `0.249097` |
| `close_below_stop` | `590` | `-9.917426` | `-24.84472` | `0.127119` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `39` | `51.063887` | `-3.0` | `0.384615` |
| `premium_entry_continuation_observation` | `2` | `1.793316` | `3.206466` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `14` | `-3.0` | `-3.0` | `0.0` |
| `below_entry_recovery_observation` | `362` | `-4.895534` | `-19.655892` | `0.309392` |
| `pullback_retest_observation` | `554` | `-4.999809` | `-20.169306` | `0.249097` |
| `neutral_location_observation` | `668` | `-5.058462` | `-19.900238` | `0.330838` |
| `invalidation_observation` | `590` | `-9.917426` | `-24.84472` | `0.127119` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `반도체_후공정장비` | `10` | `-19.319946` | `-35.219296` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `11` | `-19.199182` | `-34.670487` |
| `sector` | `Manufacture of Man-Made Fibers` | `10` | `-18.720026` | `-22.402172` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `5` | `-18.40825` | `-20.649404` |
| `theme_tags` | `원자력_설계시공` | `7` | `-18.345997` | `-22.443518` |
| `theme_tags` | `SI(시스템통합)` | `7` | `-17.706934` | `-23.845109` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `9` | `-16.295208` | `-23.752495` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `7` | `-16.239317` | `-26.84492` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `14` | `-15.347001` | `-22.012805` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `47` | `-14.830943` | `-35.27746` |
| `theme_tags` | `희소금속` | `12` | `-14.686935` | `-25.024213` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `26` | `-14.629472` | `-24.435813` |
| `sector` | `Manufacture of Semiconductor` | `47` | `-14.562359` | `-27.353052` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `9` | `-14.561028` | `-26.556719` |
| `sector` | `Computer programming, System Integration and Management Services` | `25` | `-14.528122` | `-22.967252` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `13` | `-14.278986` | `-31.570549` |
| `theme_tags` | `로봇_지능형` | `5` | `-14.240565` | `-19.700268` |
| `sector` | `Manufacture of primary battery and secondary battery` | `44` | `-13.850482` | `-25.545383` |
| `theme_tags` | `비철금속주` | `11` | `-13.578754` | `-19.299611` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `25` | `-13.549018` | `-26.451166` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
