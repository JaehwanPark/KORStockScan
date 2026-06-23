# Swing Strategy Discovery EV - 2026-06-23

- generated_at: `2026-06-23T20:40:28`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1227` / `7787` / `7787`
- labeled_sample_count: `901`
- pending_future_quote_count: `4322`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 947, 'expired_entry_no_trigger': 365, 'labeled': 123}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 2564, 'ENTERED': 2914, 'PENDING_ENTRY': 1408, 'EXITED': 901}, 'label_status_counts': {'expired_entry_no_trigger': 2564, 'pending_future_quotes': 4322, 'labeled': 901}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 947, 'expired_entry_no_trigger': 365, 'labeled': 123}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 947, 'matured_no_entry': 365, 'matured_labeled': 123}, 'bottom_rebound_pending_future_quote_count': 947, 'bottom_rebound_labeled_sample_count': 123, 'bottom_rebound_expired_entry_count': 365, 'maturity_status_counts': {'matured_no_entry': 2564, 'pending_future_quotes': 4322, 'matured_labeled': 901}, 'entry_reason_counts': {'pullback_not_touched': 1020, 'breakout_not_touched': 986, 'next_open': 1400, 'pullback_limit_touched': 1080, 'missing_next_quote': 990, 'bottom_rebound_next_open': 399, 'gap_fade_condition_not_met': 656, 'breakout_trigger_touched': 414, 'bottom_rebound_atr_pullback_not_touched': 209, 'gap_fade_limit_touched': 44, 'bottom_rebound_signal_close_retest_touched': 288, 'bottom_rebound_signal_close_retest_not_touched': 111, 'bottom_rebound_atr_pullback_touched': 190}, 'policy_exit_reason_counts': {'pullback_not_touched': 1020, 'breakout_not_touched': 986, 'need_5_quotes': 516, 'need_10_quotes': 2398, 'missing_next_quote': 990, 'gap_fade_condition_not_met': 656, 'mae_stop_touched': 562, 'bottom_rebound_atr_pullback_not_touched': 209, 'fixed_5d_close': 228, 'trailing_after_mfe_stop': 111, 'bottom_rebound_signal_close_retest_not_touched': 111}, 'source_quality_status_counts': {'ok': 3465, 'pending_future_quotes': 4322}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `111` | `8.986789` | `2.542448` | `1.0` |
| `arm06_gap_fade_risk_fixed5d` | `8` | `1.464721` | `-4.198764` | `0.5` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 9, 'total_row_count': 64, 'entry_fill_rate': 0.140625, 'expired_rate': 0.265625, 'equal_weight_avg_final_return_pct': 0.376205, 'notional_weighted_ev_pct': 0.872329, 'source_quality_adjusted_ev_pct': 0.872329, 'diagnostic_win_rate': 0.333333, 'downside_p10_pct': -4.218182, 'mae_p90_pct': -9.673903}`
- discovery_combined: `{'sample_count': 892, 'source_quality_adjusted_ev_pct': 1.250092}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `279` | `4.67386` | `-3.0` | `0.494624` |
| `wick_stop_recovered_close_above_stop` | `256` | `0.686804` | `-3.0` | `0.269531` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `366` | `-1.376375` | `-3.0` | `0.128415` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `discount_entry_observation` | `86` | `7.375893` | `-3.0` | `0.465116` |
| `momentum_chase_observation` | `54` | `6.843097` | `-3.0` | `0.592593` |
| `premium_entry_continuation_observation` | `5` | `5.144` | `-3.0` | `0.6` |
| `below_entry_recovery_observation` | `72` | `3.001327` | `-3.0` | `0.583333` |
| `neutral_location_observation` | `62` | `1.652502` | `-3.0` | `0.33871` |
| `pullback_retest_observation` | `256` | `0.686804` | `-3.0` | `0.269531` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `366` | `-1.376375` | `-3.0` | `0.128415` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `11` | `-6.339339` | `-11.828794` |
| `sector` | `Software Development and Supply` | `12` | `-5.201274` | `-10.3211` |
| `theme_tags` | `타이어` | `5` | `-4.706797` | `-7.45` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `5` | `-4.244531` | `-5.753846` |
| `sector` | `Computer programming, System Integration and Management Services` | `14` | `-4.051244` | `-8.482016` |
| `theme_tags` | `기계_공작기계` | `5` | `-3.846395` | `-3.931034` |
| `theme_tags` | `중국_내수소비 확대,화장품` | `5` | `-3.688092` | `-3.738976` |
| `theme_tags` | `증권,창투` | `6` | `-3.028664` | `-3.070175` |
| `sector` | `Road Freight Transport` | `8` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of medicinal chemicals` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `7` | `-3.0` | `-3.0` |
| `theme_tags` | `운송_항공` | `7` | `-3.0` | `-3.0` |
| `theme_tags` | `의복_아웃도어` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `바이오_줄기세포치료제` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `39` | `-2.907128` | `-3.310345` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `8` | `-2.729814` | `-4.916326` |
| `sector` | `Retail Sale of Fuel` | `7` | `-2.46527` | `-3.0` |
| `theme_tags` | `그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체` | `7` | `-2.1849` | `-3.0` |
| `sector` | `Manufacture of primary battery and secondary battery` | `14` | `-1.991881` | `-3.0` |
| `sector` | `Manufacture of Electric Lamps and Bulbs` | `13` | `-1.963307` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
