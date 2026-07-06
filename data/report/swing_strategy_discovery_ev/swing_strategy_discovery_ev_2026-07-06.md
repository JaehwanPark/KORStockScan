# Swing Strategy Discovery EV - 2026-07-06

- generated_at: `2026-07-06T20:28:26`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1639` / `10752` / `10752`
- labeled_sample_count: `1684`
- pending_future_quote_count: `3910`
- bottom_rebound_policy_exit_row_count: `1736`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 933, 'labeled': 254, 'expired_entry_no_trigger': 549}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 5158, 'EXITED': 1684, 'ENTERED': 2877, 'PENDING_ENTRY': 1033}, 'label_status_counts': {'expired_entry_no_trigger': 5158, 'pending_future_quotes': 3910, 'labeled': 1684}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 933, 'labeled': 254, 'expired_entry_no_trigger': 549}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 933, 'matured_labeled': 254, 'matured_no_entry': 549}, 'bottom_rebound_pending_future_quote_count': 933, 'bottom_rebound_labeled_sample_count': 254, 'bottom_rebound_expired_entry_count': 549, 'maturity_status_counts': {'matured_no_entry': 5158, 'pending_future_quotes': 3910, 'matured_labeled': 1684}, 'entry_reason_counts': {'gap_fade_condition_not_met': 1019, 'breakout_not_touched': 1814, 'bottom_rebound_atr_pullback_not_touched': 354, 'next_open': 2156, 'pullback_not_touched': 2193, 'breakout_trigger_touched': 342, 'gap_fade_limit_touched': 59, 'pullback_limit_touched': 1041, 'bottom_rebound_signal_close_retest_touched': 373, 'bottom_rebound_next_open': 472, 'bottom_rebound_signal_close_retest_not_touched': 99, 'bottom_rebound_atr_pullback_touched': 118, 'missing_next_quote': 712}, 'policy_exit_reason_counts': {'gap_fade_condition_not_met': 1019, 'breakout_not_touched': 1814, 'bottom_rebound_atr_pullback_not_touched': 354, 'fixed_5d_close': 795, 'fixed_10d_close': 340, 'pullback_not_touched': 2193, 'trailing_after_mfe_stop': 89, 'mae_stop_touched': 458, 'need_10_quotes': 2535, 'scale_in_recovery_10d_close': 2, 'bottom_rebound_signal_close_retest_not_touched': 99, 'need_5_quotes': 342, 'missing_next_quote': 712}, 'source_quality_status_counts': {'ok': 6842, 'pending_future_quotes': 3910}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `89` | `19.212755` | `2.771221` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 17, 'total_row_count': 72, 'entry_fill_rate': 0.236111, 'expired_rate': 0.555556, 'equal_weight_avg_final_return_pct': -10.02249, 'notional_weighted_ev_pct': -10.41753, 'source_quality_adjusted_ev_pct': -10.41753, 'diagnostic_win_rate': 0.117647, 'downside_p10_pct': -28.027627, 'mae_p90_pct': -34.021148}`
- discovery_combined: `{'sample_count': 1667, 'source_quality_adjusted_ev_pct': -3.76234}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `759` | `-0.874278` | `-14.42953` | `0.351779` |
| `wick_stop_recovered_close_above_stop` | `493` | `-4.313191` | `-15.967742` | `0.200811` |
| `close_below_stop` | `432` | `-7.945285` | `-22.865415` | `0.12963` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `86` | `16.530938` | `-7.970147` | `0.534884` |
| `discount_entry_observation` | `223` | `0.163639` | `-8.307287` | `0.363229` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `below_entry_recovery_observation` | `256` | `-4.071172` | `-15.873628` | `0.375` |
| `pullback_retest_observation` | `493` | `-4.313191` | `-15.967742` | `0.200811` |
| `premium_entry_continuation_observation` | `5` | `-5.4104` | `-11.195444` | `0.2` |
| `neutral_location_observation` | `189` | `-6.090503` | `-16.524823` | `0.227513` |
| `invalidation_observation` | `432` | `-7.945285` | `-22.865415` | `0.12963` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Television Broadcasting` | `5` | `-20.114213` | `-27.288719` |
| `sector` | `Computer programming, System Integration and Management Services` | `23` | `-15.524341` | `-30.255101` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `10` | `-15.239066` | `-33.811631` |
| `theme_tags` | `미디어_디지털방송전환` | `7` | `-14.653476` | `-23.801147` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `9` | `-14.192409` | `-27.86644` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `7` | `-13.808577` | `-19.9801` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `13` | `-13.798375` | `-22.347357` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `10` | `-13.775715` | `-25.854098` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `8` | `-13.714578` | `-24.757702` |
| `sector` | `Manufacture of Gas, Distribution of Gaseous Fuel Through Mains` | `5` | `-13.125846` | `-7.89161` |
| `theme_tags` | `반도체_후공정장비` | `11` | `-13.047394` | `-26.519007` |
| `sector` | `Manufacture of Semiconductor` | `38` | `-12.619275` | `-27.351295` |
| `sector` | `Manufacture of Man-Made Fibers` | `10` | `-12.50512` | `-18.783069` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `21` | `-12.442135` | `-19.433962` |
| `theme_tags` | `태양광_폴리실리콘` | `10` | `-11.856789` | `-27.856822` |
| `sector` | `Manufacture of Plastics and Synethetic Rubber in Primary forms` | `7` | `-11.711712` | `-11.711712` |
| `theme_tags` | `그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체` | `13` | `-11.439972` | `-21.587302` |
| `sector` | `Telecommunications` | `7` | `-10.684179` | `-15.86927` |
| `sector` | `Manufacture of Other Transport Equipment` | `7` | `-10.330475` | `-8.708278` |
| `theme_tags` | `SI(시스템통합),스마트 그리드` | `11` | `-10.187239` | `-17.884615` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
