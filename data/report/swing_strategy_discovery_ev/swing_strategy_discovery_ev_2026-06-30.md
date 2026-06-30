# Swing Strategy Discovery EV - 2026-06-30

- generated_at: `2026-06-30T20:23:57`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1406` / `9219` / `9219`
- labeled_sample_count: `1254`
- pending_future_quote_count: `3962`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'expired_entry_no_trigger': 435, 'labeled': 153, 'pending_future_quotes': 847}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 4003, 'ENTERED': 3159, 'EXITED': 1254, 'PENDING_ENTRY': 803}, 'label_status_counts': {'expired_entry_no_trigger': 4003, 'labeled': 1254, 'pending_future_quotes': 3962}, 'bottom_rebound_label_status_counts': {'expired_entry_no_trigger': 435, 'labeled': 153, 'pending_future_quotes': 847}, 'bottom_rebound_maturity_status_counts': {'matured_no_entry': 435, 'matured_labeled': 153, 'pending_future_quotes': 847}, 'bottom_rebound_pending_future_quote_count': 847, 'bottom_rebound_labeled_sample_count': 153, 'bottom_rebound_expired_entry_count': 435, 'maturity_status_counts': {'matured_no_entry': 4003, 'matured_labeled': 1254, 'pending_future_quotes': 3962}, 'entry_reason_counts': {'bottom_rebound_atr_pullback_not_touched': 269, 'bottom_rebound_atr_pullback_touched': 164, 'bottom_rebound_next_open': 433, 'bottom_rebound_signal_close_retest_touched': 346, 'bottom_rebound_signal_close_retest_not_touched': 87, 'missing_next_quote': 544, 'next_open': 1844, 'pullback_not_touched': 1518, 'gap_fade_condition_not_met': 866, 'breakout_not_touched': 1522, 'gap_fade_limit_touched': 56, 'breakout_trigger_touched': 322, 'pullback_limit_touched': 1248}, 'policy_exit_reason_counts': {'bottom_rebound_atr_pullback_not_touched': 269, 'mae_stop_touched': 632, 'need_10_quotes': 2733, 'bottom_rebound_signal_close_retest_not_touched': 87, 'missing_next_quote': 544, 'fixed_5d_close': 552, 'pullback_not_touched': 1518, 'gap_fade_condition_not_met': 866, 'breakout_not_touched': 1522, 'need_5_quotes': 426, 'trailing_after_mfe_stop': 70}, 'source_quality_status_counts': {'ok': 5257, 'pending_future_quotes': 3962}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `70` | `7.762784` | `2.929843` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 11, 'total_row_count': 64, 'entry_fill_rate': 0.171875, 'expired_rate': 0.40625, 'equal_weight_avg_final_return_pct': -4.445811, 'notional_weighted_ev_pct': -4.581635, 'source_quality_adjusted_ev_pct': -4.581635, 'diagnostic_win_rate': 0.090909, 'downside_p10_pct': -6.716418, 'mae_p90_pct': -17.412935}`
- discovery_combined: `{'sample_count': 1243, 'source_quality_adjusted_ev_pct': -3.679296}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `412` | `-2.713554` | `-12.070494` | `0.174757` |
| `no_touch` | `534` | `-3.756897` | `-14.642762` | `0.219101` |
| `close_below_stop` | `308` | `-5.026674` | `-16.033022` | `0.113636` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `42` | `4.830158` | `-4.528473` | `0.404762` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `155` | `-1.266734` | `-8.771015` | `0.187097` |
| `pullback_retest_observation` | `412` | `-2.713554` | `-12.070494` | `0.174757` |
| `premium_entry_continuation_observation` | `3` | `-2.991473` | `-11.716444` | `0.333333` |
| `below_entry_recovery_observation` | `166` | `-4.718007` | `-15.388715` | `0.301205` |
| `invalidation_observation` | `308` | `-5.026674` | `-16.033022` | `0.113636` |
| `neutral_location_observation` | `168` | `-6.812844` | `-16.523116` | `0.119048` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `태양광_폴리실리콘` | `5` | `-12.551786` | `-29.20229` |
| `sector` | `Manufacture of Man-Made Fibers` | `8` | `-11.746302` | `-18.783069` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `7` | `-11.703979` | `-24.806469` |
| `sector` | `Manufacture of Other Transport Equipment` | `7` | `-11.154682` | `-8.708278` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `11` | `-10.973964` | `-19.755245` |
| `sector` | `Audio Publishing and Original Master Recordings` | `9` | `-10.664608` | `-18.56833` |
| `theme_tags` | `원자력_설계시공` | `7` | `-10.135556` | `-15.033012` |
| `sector` | `Telecommunications` | `5` | `-9.635198` | `-13.173356` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `6` | `-9.512014` | `-17.956743` |
| `sector` | `Manufacture of Footwear and Parts of Footwear` | `5` | `-9.371507` | `-18.421053` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `20` | `-9.262042` | `-11.058255` |
| `theme_tags` | `의복_아웃도어` | `11` | `-8.671046` | `-18.783069` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `10` | `-8.650599` | `-16.903073` |
| `theme_tags` | `미디어_디지털방송전환` | `5` | `-8.46219` | `-13.201783` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `7` | `-8.426278` | `-33.58605` |
| `theme_tags` | `비철금속주` | `7` | `-8.344194` | `-12.205372` |
| `sector` | `Computer programming, System Integration and Management Services` | `22` | `-8.320345` | `-20.841152` |
| `theme_tags` | `SI(시스템통합)` | `7` | `-8.198677` | `-16.202532` |
| `sector` | `Heavy Construction` | `7` | `-7.895443` | `-16.887986` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `5` | `-7.789275` | `-14.94152` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
