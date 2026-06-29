# Swing Strategy Discovery EV - 2026-06-29

- generated_at: `2026-06-29T20:21:33`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1356` / `8819` / `8819`
- labeled_sample_count: `1121`
- pending_future_quote_count: `3817`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 803, 'expired_entry_no_trigger': 464, 'labeled': 168}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 3881, 'PENDING_ENTRY': 875, 'ENTERED': 2942, 'EXITED': 1121}, 'label_status_counts': {'expired_entry_no_trigger': 3881, 'pending_future_quotes': 3817, 'labeled': 1121}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 803, 'expired_entry_no_trigger': 464, 'labeled': 168}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 803, 'matured_no_entry': 464, 'matured_labeled': 168}, 'bottom_rebound_pending_future_quote_count': 803, 'bottom_rebound_labeled_sample_count': 168, 'bottom_rebound_expired_entry_count': 464, 'maturity_status_counts': {'matured_no_entry': 3881, 'pending_future_quotes': 3817, 'matured_labeled': 1121}, 'entry_reason_counts': {'pullback_not_touched': 1431, 'missing_next_quote': 544, 'bottom_rebound_next_open': 433, 'bottom_rebound_atr_pullback_not_touched': 253, 'gap_fade_condition_not_met': 835, 'breakout_trigger_touched': 180, 'next_open': 1744, 'pullback_limit_touched': 1185, 'breakout_not_touched': 1564, 'gap_fade_limit_touched': 37, 'bottom_rebound_signal_close_retest_touched': 304, 'bottom_rebound_signal_close_retest_not_touched': 129, 'bottom_rebound_atr_pullback_touched': 180}, 'policy_exit_reason_counts': {'pullback_not_touched': 1431, 'missing_next_quote': 544, 'need_10_quotes': 2511, 'bottom_rebound_atr_pullback_not_touched': 253, 'gap_fade_condition_not_met': 835, 'mae_stop_touched': 599, 'fixed_5d_close': 478, 'breakout_not_touched': 1564, 'trailing_after_mfe_stop': 44, 'bottom_rebound_signal_close_retest_not_touched': 129, 'need_5_quotes': 431}, 'source_quality_status_counts': {'ok': 5002, 'pending_future_quotes': 3817}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `44` | `10.254728` | `3.146525` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 11, 'total_row_count': 64, 'entry_fill_rate': 0.171875, 'expired_rate': 0.4375, 'equal_weight_avg_final_return_pct': -1.179863, 'notional_weighted_ev_pct': -0.872928, 'source_quality_adjusted_ev_pct': -0.872928, 'diagnostic_win_rate': 0.272727, 'downside_p10_pct': -3.0, 'mae_p90_pct': -13.341613}`
- discovery_combined: `{'sample_count': 1110, 'source_quality_adjusted_ev_pct': -3.728549}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `330` | `-2.834444` | `-11.845315` | `0.151515` |
| `no_touch` | `484` | `-3.583187` | `-16.888889` | `0.235537` |
| `close_below_stop` | `307` | `-4.726036` | `-15.669028` | `0.110749` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `discount_entry_observation` | `174` | `0.046679` | `-10.955567` | `0.275862` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `momentum_chase_observation` | `40` | `-2.623315` | `-17.161217` | `0.325` |
| `pullback_retest_observation` | `330` | `-2.834444` | `-11.845315` | `0.151515` |
| `below_entry_recovery_observation` | `185` | `-3.858555` | `-14.702563` | `0.2` |
| `invalidation_observation` | `307` | `-4.726036` | `-15.669028` | `0.110749` |
| `premium_entry_continuation_observation` | `2` | `-6.193525` | `-19.517751` | `0.0` |
| `neutral_location_observation` | `83` | `-8.471884` | `-22.730446` | `0.192771` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Other Transport Equipment` | `7` | `-14.524241` | `-11.066968` |
| `theme_tags` | `SI(시스템통합)` | `5` | `-13.357772` | `-18.557177` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `10` | `-13.343356` | `-19.706799` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `10` | `-12.60794` | `-26.944889` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `6` | `-12.479405` | `-23.752495` |
| `theme_tags` | `비철금속주` | `6` | `-11.828794` | `-11.828794` |
| `theme_tags` | `원자력_설계시공` | `5` | `-11.421079` | `-21.532847` |
| `sector` | `Manufacture of Sewn Wearing Apparel, Except Fur Apparel` | `6` | `-11.307618` | `-11.603576` |
| `theme_tags` | `의복_아웃도어` | `8` | `-10.349314` | `-20.920502` |
| `sector` | `Manufacture of Man-Made Fibers` | `8` | `-10.253982` | `-20.920502` |
| `theme_tags` | `증권,창투` | `6` | `-10.172879` | `-17.986503` |
| `sector` | `Heavy Construction` | `6` | `-10.06402` | `-15.620456` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `6` | `-9.34451` | `-16.041524` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `19` | `-9.336987` | `-11.828794` |
| `sector` | `Software Development and Supply` | `15` | `-8.91604` | `-14.891041` |
| `sector` | `Manufacture of Other Chemical Products` | `50` | `-8.669851` | `-21.562536` |
| `theme_tags` | `신약개발/기술수출` | `6` | `-8.387296` | `-15.949367` |
| `sector` | `Manufacture of Footwear and Parts of Footwear` | `5` | `-8.292703` | `-18.462463` |
| `theme_tags` | `중국_내수소비 확대,화장품` | `5` | `-8.098294` | `-10.760277` |
| `block_reason` | `blocked_gatekeeper_reject` | `91` | `-8.02263` | `-17.44325` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
