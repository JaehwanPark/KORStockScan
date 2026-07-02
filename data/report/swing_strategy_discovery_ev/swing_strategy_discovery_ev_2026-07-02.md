# Swing Strategy Discovery EV - 2026-07-02

- generated_at: `2026-07-02T20:21:50`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1484` / `9843` / `9843`
- labeled_sample_count: `1361`
- pending_future_quote_count: `3957`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 795, 'expired_entry_no_trigger': 497, 'labeled': 143}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 3043, 'EXPIRED': 4525, 'PENDING_ENTRY': 914, 'EXITED': 1361}, 'label_status_counts': {'pending_future_quotes': 3957, 'expired_entry_no_trigger': 4525, 'labeled': 1361}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 795, 'expired_entry_no_trigger': 497, 'labeled': 143}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 795, 'matured_no_entry': 497, 'matured_labeled': 143}, 'bottom_rebound_pending_future_quote_count': 795, 'bottom_rebound_labeled_sample_count': 143, 'bottom_rebound_expired_entry_count': 497, 'maturity_status_counts': {'pending_future_quotes': 3957, 'matured_no_entry': 4525, 'matured_labeled': 1361}, 'entry_reason_counts': {'bottom_rebound_next_open': 433, 'bottom_rebound_signal_close_retest_touched': 341, 'bottom_rebound_atr_pullback_not_touched': 309, 'bottom_rebound_signal_close_retest_not_touched': 92, 'missing_next_quote': 624, 'gap_fade_limit_touched': 59, 'next_open': 1980, 'pullback_not_touched': 1875, 'breakout_not_touched': 1608, 'gap_fade_condition_not_met': 931, 'breakout_trigger_touched': 372, 'pullback_limit_touched': 1095, 'bottom_rebound_atr_pullback_touched': 124}, 'policy_exit_reason_counts': {'need_10_quotes': 2670, 'bottom_rebound_atr_pullback_not_touched': 309, 'bottom_rebound_signal_close_retest_not_touched': 92, 'missing_next_quote': 624, 'fixed_5d_close': 676, 'pullback_not_touched': 1875, 'breakout_not_touched': 1608, 'gap_fade_condition_not_met': 931, 'mae_stop_touched': 486, 'fixed_10d_close': 98, 'trailing_after_mfe_stop': 101, 'need_5_quotes': 373}, 'source_quality_status_counts': {'pending_future_quotes': 3957, 'ok': 5886}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `101` | `18.00695` | `2.461913` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 14, 'total_row_count': 64, 'entry_fill_rate': 0.21875, 'expired_rate': 0.484375, 'equal_weight_avg_final_return_pct': -8.990006, 'notional_weighted_ev_pct': -9.940126, 'source_quality_adjusted_ev_pct': -9.940126, 'diagnostic_win_rate': 0.071429, 'downside_p10_pct': -22.293801, 'mae_p90_pct': -28.258822}`
- discovery_combined: `{'sample_count': 1347, 'source_quality_adjusted_ev_pct': -3.375615}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `574` | `-1.183041` | `-14.695946` | `0.268293` |
| `wick_stop_recovered_close_above_stop` | `437` | `-4.17042` | `-15.976451` | `0.199085` |
| `close_below_stop` | `350` | `-6.281462` | `-19.433962` | `0.148571` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `78` | `21.798766` | `-3.0` | `0.551282` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `128` | `-1.152334` | `-10.542636` | `0.234375` |
| `pullback_retest_observation` | `437` | `-4.17042` | `-15.976451` | `0.199085` |
| `below_entry_recovery_observation` | `186` | `-4.621756` | `-16.077739` | `0.333333` |
| `premium_entry_continuation_observation` | `5` | `-5.4104` | `-11.195444` | `0.2` |
| `invalidation_observation` | `350` | `-6.281462` | `-19.433962` | `0.148571` |
| `neutral_location_observation` | `177` | `-7.015302` | `-16.5341` | `0.101695` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Other Transport Equipment` | `6` | `-17.270694` | `-10.135347` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `10` | `-15.202674` | `-33.703187` |
| `theme_tags` | `미디어_디지털방송전환` | `6` | `-14.653476` | `-25.544933` |
| `theme_tags` | `태양광_폴리실리콘` | `6` | `-14.340497` | `-28.963833` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `8` | `-12.88322` | `-24.757702` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `10` | `-11.843563` | `-18.157773` |
| `sector` | `Manufacture of Man-Made Fibers` | `9` | `-11.779505` | `-18.783069` |
| `sector` | `Computer programming, System Integration and Management Services` | `23` | `-11.511184` | `-22.098083` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `13` | `-10.976817` | `-21.544799` |
| `theme_tags` | `원자력_설계시공` | `5` | `-10.762281` | `-15.033012` |
| `sector` | `Telecommunications` | `7` | `-10.684179` | `-15.86927` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `21` | `-10.523491` | `-19.433962` |
| `theme_tags` | `반도체_후공정장비` | `13` | `-10.313526` | `-25.161928` |
| `sector` | `Manufacture of Semiconductor` | `29` | `-9.871421` | `-22.943813` |
| `sector` | `Retail Sale of Fuel` | `6` | `-9.742445` | `-15.378359` |
| `sector` | `Audio Publishing and Original Master Recordings` | `11` | `-9.736665` | `-18.56833` |
| `sector` | `Manufacture of Special-Purpose Machinery` | `26` | `-9.655046` | `-24.809932` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `6` | `-9.512014` | `-17.956743` |
| `theme_tags` | `자원개발 E&P` | `19` | `-9.400589` | `-19.299025` |
| `theme_tags` | `자동차_전장화 수혜` | `9` | `-9.345509` | `-17.654474` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
