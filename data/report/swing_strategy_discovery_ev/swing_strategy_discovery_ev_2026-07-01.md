# Swing Strategy Discovery EV - 2026-07-01

- generated_at: `2026-07-01T20:24:22`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1456` / `9619` / `9619`
- labeled_sample_count: `1182`
- pending_future_quote_count: `4078`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 801, 'expired_entry_no_trigger': 502, 'labeled': 132}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 4359, 'ENTERED': 3008, 'PENDING_ENTRY': 1070, 'EXITED': 1182}, 'label_status_counts': {'expired_entry_no_trigger': 4359, 'pending_future_quotes': 4078, 'labeled': 1182}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 801, 'expired_entry_no_trigger': 502, 'labeled': 132}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 801, 'matured_no_entry': 502, 'matured_labeled': 132}, 'bottom_rebound_pending_future_quote_count': 801, 'bottom_rebound_labeled_sample_count': 132, 'bottom_rebound_expired_entry_count': 502, 'maturity_status_counts': {'matured_no_entry': 4359, 'pending_future_quotes': 4078, 'matured_labeled': 1182}, 'entry_reason_counts': {'breakout_not_touched': 1586, 'bottom_rebound_next_open': 433, 'bottom_rebound_signal_close_retest_not_touched': 132, 'bottom_rebound_atr_pullback_not_touched': 283, 'missing_next_quote': 800, 'next_open': 1880, 'pullback_not_touched': 1734, 'gap_fade_condition_not_met': 894, 'breakout_trigger_touched': 294, 'pullback_limit_touched': 1086, 'gap_fade_limit_touched': 46, 'bottom_rebound_signal_close_retest_touched': 301, 'bottom_rebound_atr_pullback_touched': 150}, 'policy_exit_reason_counts': {'breakout_not_touched': 1586, 'need_10_quotes': 2626, 'bottom_rebound_signal_close_retest_not_touched': 132, 'bottom_rebound_atr_pullback_not_touched': 283, 'missing_next_quote': 800, 'fixed_5d_close': 604, 'need_5_quotes': 382, 'pullback_not_touched': 1734, 'gap_fade_condition_not_met': 894, 'mae_stop_touched': 497, 'trailing_after_mfe_stop': 81}, 'source_quality_status_counts': {'ok': 5541, 'pending_future_quotes': 4078}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `81` | `18.974022` | `2.952943` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 10, 'total_row_count': 64, 'entry_fill_rate': 0.15625, 'expired_rate': 0.4375, 'equal_weight_avg_final_return_pct': -1.323257, 'notional_weighted_ev_pct': -1.059332, 'source_quality_adjusted_ev_pct': -1.059332, 'diagnostic_win_rate': 0.3, 'downside_p10_pct': -3.609091, 'mae_p90_pct': -15.884018}`
- discovery_combined: `{'sample_count': 1172, 'source_quality_adjusted_ev_pct': -3.634846}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `504` | `-1.229835` | `-17.315317` | `0.299603` |
| `wick_stop_recovered_close_above_stop` | `347` | `-2.781026` | `-14.204681` | `0.175793` |
| `close_below_stop` | `331` | `-8.129984` | `-21.793103` | `0.099698` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `66` | `14.779045` | `-12.356254` | `0.530303` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `153` | `-0.200271` | `-12.074826` | `0.333333` |
| `pullback_retest_observation` | `347` | `-2.781026` | `-14.204681` | `0.175793` |
| `below_entry_recovery_observation` | `171` | `-3.82019` | `-14.807302` | `0.233918` |
| `premium_entry_continuation_observation` | `4` | `-5.300067` | `-17.59898` | `0.5` |
| `neutral_location_observation` | `110` | `-8.021377` | `-21.517777` | `0.209091` |
| `invalidation_observation` | `331` | `-8.129984` | `-21.793103` | `0.099698` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Other Transport Equipment` | `6` | `-23.167421` | `-13.083711` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `5` | `-14.319188` | `-23.752495` |
| `theme_tags` | `원자력_설계시공` | `7` | `-14.237168` | `-22.443518` |
| `theme_tags` | `SI(시스템통합)` | `5` | `-14.136138` | `-20.141962` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `7` | `-13.013912` | `-27.871798` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `9` | `-12.203905` | `-32.556873` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `10` | `-11.900744` | `-19.706799` |
| `theme_tags` | `비철금속주` | `6` | `-11.828794` | `-11.828794` |
| `sector` | `Heavy Construction` | `7` | `-11.514895` | `-16.287873` |
| `theme_tags` | `증권,창투` | `5` | `-11.39686` | `-18.484629` |
| `sector` | `Manufacture of Man-Made Fibers` | `7` | `-11.287045` | `-20.920502` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `20` | `-11.070638` | `-13.190557` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `12` | `-10.648411` | `-26.765799` |
| `theme_tags` | `방위산업,조선_Eco선` | `5` | `-9.820943` | `-15.023146` |
| `theme_tags` | `자동차_전장화 수혜` | `9` | `-9.025852` | `-21.793103` |
| `theme_tags` | `신약개발/기술수출` | `7` | `-8.983583` | `-15.949367` |
| `sector` | `Manufacture of Other Chemical Products` | `54` | `-8.852911` | `-20.420219` |
| `sector` | `Manufacture of General Purpose Machinery` | `39` | `-8.670889` | `-24.915705` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `8` | `-8.641986` | `-17.99135` |
| `sector` | `Computer programming, System Integration and Management Services` | `15` | `-8.611631` | `-17.581588` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
