# Swing Strategy Discovery EV - 2026-07-10

- generated_at: `2026-07-11T13:04:24`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1933` / `12376` / `12376`
- labeled_sample_count: `2362`
- pending_future_quote_count: `3599`
- bottom_rebound_policy_exit_row_count: `2288`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1120, 'expired_entry_no_trigger': 681, 'labeled': 487}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 6415, 'PENDING_ENTRY': 757, 'ENTERED': 2842, 'EXITED': 2362}, 'label_status_counts': {'pending_future_quotes': 3599, 'expired_entry_no_trigger': 6415, 'labeled': 2362}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1120, 'expired_entry_no_trigger': 681, 'labeled': 487}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1120, 'matured_no_entry': 681, 'matured_labeled': 487}, 'bottom_rebound_pending_future_quote_count': 1120, 'bottom_rebound_labeled_sample_count': 487, 'bottom_rebound_expired_entry_count': 681, 'maturity_status_counts': {'pending_future_quotes': 3599, 'matured_no_entry': 6415, 'matured_labeled': 2362}, 'entry_reason_counts': {'bottom_rebound_atr_pullback_not_touched': 460, 'gap_fade_condition_not_met': 1178, 'breakout_not_touched': 2126, 'bottom_rebound_signal_close_retest_not_touched': 207, 'pullback_not_touched': 2769, 'bottom_rebound_next_open': 672, 'next_open': 2482, 'breakout_trigger_touched': 356, 'pullback_limit_touched': 954, 'gap_fade_limit_touched': 63, 'bottom_rebound_signal_close_retest_touched': 465, 'bottom_rebound_atr_pullback_touched': 212, 'missing_next_quote': 432}, 'policy_exit_reason_counts': {'bottom_rebound_atr_pullback_not_touched': 460, 'gap_fade_condition_not_met': 1178, 'breakout_not_touched': 2126, 'bottom_rebound_signal_close_retest_not_touched': 207, 'pullback_not_touched': 2769, 'fixed_10d_close': 784, 'fixed_5d_close': 968, 'trailing_after_mfe_stop': 90, 'mae_stop_touched': 515, 'scale_in_recovery_10d_close': 2, 'trailing_after_mfe_10d_close': 2, 'need_10_quotes': 2506, 'need_5_quotes': 336, 'mae_stop_time_stop_10d_close': 1, 'missing_next_quote': 432}, 'source_quality_status_counts': {'pending_future_quotes': 3599, 'ok': 8777}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `92` | `15.811705` | `2.571158` | `0.978261` |
| `arm08_breakout_risk_mae_time` | `143` | `0.823097` | `-3.0` | `0.006993` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 19, 'total_row_count': 96, 'entry_fill_rate': 0.197917, 'expired_rate': 0.395833, 'equal_weight_avg_final_return_pct': -4.686297, 'notional_weighted_ev_pct': -5.110124, 'source_quality_adjusted_ev_pct': -5.110124, 'diagnostic_win_rate': 0.315789, 'downside_p10_pct': -18.472302, 'mae_p90_pct': -23.636623}`
- discovery_combined: `{'sample_count': 2343, 'source_quality_adjusted_ev_pct': -5.280259}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1135` | `-3.138473` | `-19.353993` | `0.324229` |
| `wick_stop_recovered_close_above_stop` | `577` | `-4.810994` | `-20.104723` | `0.240901` |
| `close_below_stop` | `650` | `-9.388981` | `-23.530952` | `0.123077` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `45` | `44.97946` | `-3.0` | `0.377778` |
| `premium_entry_continuation_observation` | `2` | `1.224502` | `2.923214` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `26` | `-3.0` | `-3.0` | `0.0` |
| `below_entry_recovery_observation` | `372` | `-4.495074` | `-19.04863` | `0.325269` |
| `pullback_retest_observation` | `577` | `-4.810994` | `-20.104723` | `0.240901` |
| `neutral_location_observation` | `690` | `-5.022166` | `-19.756916` | `0.330435` |
| `invalidation_observation` | `650` | `-9.388981` | `-23.530952` | `0.123077` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `반도체_후공정장비` | `10` | `-19.319946` | `-35.219296` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `11` | `-19.182695` | `-34.670487` |
| `sector` | `Manufacture of Man-Made Fibers` | `10` | `-18.720026` | `-22.402172` |
| `theme_tags` | `SI(시스템통합)` | `7` | `-17.706934` | `-23.845109` |
| `theme_tags` | `원자력_설계시공` | `8` | `-16.778086` | `-22.21585` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `9` | `-16.295208` | `-23.752495` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `16` | `-15.347001` | `-21.367747` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `7` | `-15.209416` | `-26.84492` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `48` | `-14.695361` | `-35.183585` |
| `theme_tags` | `희소금속` | `12` | `-14.686935` | `-25.024213` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `31` | `-14.629472` | `-23.425197` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `9` | `-14.561028` | `-26.556719` |
| `sector` | `Manufacture of Semiconductor` | `48` | `-14.509376` | `-27.304263` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `7` | `-14.31232` | `-20.357096` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `13` | `-14.278986` | `-31.570549` |
| `theme_tags` | `로봇_지능형` | `7` | `-14.240565` | `-19.67748` |
| `sector` | `Computer programming, System Integration and Management Services` | `26` | `-14.172187` | `-22.919864` |
| `theme_tags` | `비철금속주` | `12` | `-13.578754` | `-18.579214` |
| `sector` | `Manufacture of primary battery and secondary battery` | `46` | `-13.442489` | `-25.40444` |
| `sector` | `Building of Ships and Boats` | `30` | `-13.435187` | `-25.835562` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
