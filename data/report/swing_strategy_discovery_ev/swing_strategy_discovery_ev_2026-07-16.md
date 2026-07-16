# Swing Strategy Discovery EV - 2026-07-16

- generated_at: `2026-07-16T21:26:59`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `2405` / `15701` / `15701`
- labeled_sample_count: `3049`
- pending_future_quote_count: `4953`
- bottom_rebound_policy_exit_row_count: `3045`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1380, 'expired_entry_no_trigger': 905, 'labeled': 760}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1644, 'EXPIRED': 7699, 'EXITED': 3049, 'ENTERED': 3309}, 'label_status_counts': {'pending_future_quotes': 4953, 'expired_entry_no_trigger': 7699, 'labeled': 3049}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1380, 'expired_entry_no_trigger': 905, 'labeled': 760}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1380, 'matured_no_entry': 905, 'matured_labeled': 760}, 'bottom_rebound_pending_future_quote_count': 1380, 'bottom_rebound_labeled_sample_count': 760, 'bottom_rebound_expired_entry_count': 905, 'maturity_status_counts': {'pending_future_quotes': 4953, 'matured_no_entry': 7699, 'matured_labeled': 3049}, 'entry_reason_counts': {'missing_next_quote': 923, 'bottom_rebound_atr_pullback_not_touched': 543, 'bottom_rebound_signal_close_retest_touched': 579, 'bottom_rebound_next_open': 790, 'bottom_rebound_signal_close_retest_not_touched': 211, 'next_open': 3102, 'pullback_not_touched': 3483, 'breakout_not_touched': 2726, 'bottom_rebound_atr_pullback_touched': 247, 'gap_fade_condition_not_met': 1457, 'gap_fade_limit_touched': 94, 'breakout_trigger_touched': 376, 'pullback_limit_touched': 1170}, 'policy_exit_reason_counts': {'missing_next_quote': 923, 'bottom_rebound_atr_pullback_not_touched': 543, 'fixed_10d_close': 1290, 'bottom_rebound_signal_close_retest_not_touched': 211, 'need_10_quotes': 2830, 'pullback_not_touched': 3483, 'breakout_not_touched': 2726, 'mae_stop_touched': 507, 'need_5_quotes': 479, 'fixed_5d_close': 1166, 'gap_fade_condition_not_met': 1457, 'trailing_after_mfe_10d_close': 5, 'trailing_after_mfe_stop': 77, 'mae_stop_time_stop_10d_close': 1, 'scale_in_recovery_10d_close': 3}, 'source_quality_status_counts': {'pending_future_quotes': 4953, 'ok': 10748}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `82` | `15.17205` | `2.377239` | `0.939024` |
| `arm08_breakout_risk_mae_time` | `120` | `1.157337` | `-3.0` | `0.008333` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 20, 'total_row_count': 96, 'entry_fill_rate': 0.208333, 'expired_rate': 0.635417, 'equal_weight_avg_final_return_pct': -9.08767, 'notional_weighted_ev_pct': -9.43624, 'source_quality_adjusted_ev_pct': -9.43624, 'diagnostic_win_rate': 0.25, 'downside_p10_pct': -23.502203, 'mae_p90_pct': -27.94768}`
- discovery_combined: `{'sample_count': 3029, 'source_quality_adjusted_ev_pct': -6.85279}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `1450` | `-3.905516` | `-19.158073` | `0.325517` |
| `wick_stop_recovered_close_above_stop` | `750` | `-6.134586` | `-21.337864` | `0.201333` |
| `close_below_stop` | `849` | `-11.999564` | `-28.20896` | `0.122497` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `119` | `10.75708` | `-17.296875` | `0.394958` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `379` | `-3.150777` | `-18.812785` | `0.382586` |
| `below_entry_recovery_observation` | `434` | `-4.899137` | `-20.348448` | `0.327189` |
| `premium_entry_continuation_observation` | `14` | `-5.925342` | `-15.150256` | `0.285714` |
| `pullback_retest_observation` | `750` | `-6.134586` | `-21.337864` | `0.201333` |
| `neutral_location_observation` | `504` | `-7.303701` | `-19.055555` | `0.265873` |
| `invalidation_observation` | `849` | `-11.999564` | `-28.20896` | `0.122497` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `14` | `-24.083891` | `-50.31122` |
| `theme_tags` | `방위산업,조선_Eco선,조선_해양플랜트` | `5` | `-22.720136` | `-34.382567` |
| `sector` | `Transit and Ground Passenger Transportation` | `5` | `-19.547832` | `-25.364576` |
| `sector` | `Manufacture of Man-Made Fibers` | `11` | `-18.720026` | `-22.036262` |
| `theme_tags` | `원자력_설계시공` | `10` | `-17.901498` | `-24.895238` |
| `theme_tags` | `SI(시스템통합)` | `11` | `-17.551221` | `-22.682927` |
| `sector` | `Other Specialized Wholesale` | `28` | `-17.490063` | `-32.828283` |
| `theme_tags` | `2차전지_소재(양극화물질등),온실가스배출저감` | `15` | `-17.366381` | `-34.149963` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `9` | `-16.859985` | `-24.444444` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `12` | `-16.475856` | `-28.073511` |
| `theme_tags` | `희소금속` | `15` | `-16.249148` | `-25.756798` |
| `theme_tags` | `휴대폰_수동부품` | `9` | `-16.016038` | `-22.946175` |
| `theme_tags` | `반도체_후공정장비` | `16` | `-15.660298` | `-36.05547` |
| `sector` | `Computer programming, System Integration and Management Services` | `29` | `-15.531431` | `-23.643118` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `14` | `-15.450802` | `-32.0` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `12` | `-14.761355` | `-23.752495` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `10` | `-14.653294` | `-24.759358` |
| `theme_tags` | `로봇_지능형` | `6` | `-14.240565` | `-19.688874` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `41` | `-14.18706` | `-29.964851` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `43` | `-14.167332` | `-25.042183` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
