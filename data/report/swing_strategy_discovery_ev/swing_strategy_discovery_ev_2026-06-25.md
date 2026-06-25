# Swing Strategy Discovery EV - 2026-06-25

- generated_at: `2026-06-25T21:39:08`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1288` / `8275` / `8275`
- labeled_sample_count: `1024`
- pending_future_quote_count: `3893`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'expired_entry_no_trigger': 412, 'pending_future_quotes': 844, 'labeled': 179}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 3358, 'ENTERED': 2948, 'PENDING_ENTRY': 945, 'EXITED': 1024}, 'label_status_counts': {'expired_entry_no_trigger': 3358, 'pending_future_quotes': 3893, 'labeled': 1024}, 'bottom_rebound_label_status_counts': {'expired_entry_no_trigger': 412, 'pending_future_quotes': 844, 'labeled': 179}, 'bottom_rebound_maturity_status_counts': {'matured_no_entry': 412, 'pending_future_quotes': 844, 'matured_labeled': 179}, 'bottom_rebound_pending_future_quote_count': 844, 'bottom_rebound_labeled_sample_count': 179, 'bottom_rebound_expired_entry_count': 412, 'maturity_status_counts': {'matured_no_entry': 3358, 'pending_future_quotes': 3893, 'matured_labeled': 1024}, 'entry_reason_counts': {'bottom_rebound_atr_pullback_not_touched': 228, 'bottom_rebound_next_open': 433, 'bottom_rebound_signal_close_retest_not_touched': 120, 'missing_next_quote': 488, 'pullback_not_touched': 1293, 'next_open': 1622, 'pullback_limit_touched': 1140, 'breakout_not_touched': 1390, 'gap_fade_condition_not_met': 784, 'breakout_trigger_touched': 232, 'bottom_rebound_signal_close_retest_touched': 313, 'gap_fade_limit_touched': 27, 'bottom_rebound_atr_pullback_touched': 205}, 'policy_exit_reason_counts': {'bottom_rebound_atr_pullback_not_touched': 228, 'need_10_quotes': 2455, 'bottom_rebound_signal_close_retest_not_touched': 120, 'missing_next_quote': 488, 'pullback_not_touched': 1293, 'fixed_5d_close': 345, 'mae_stop_touched': 620, 'breakout_not_touched': 1390, 'gap_fade_condition_not_met': 784, 'trailing_after_mfe_stop': 59, 'need_5_quotes': 493}, 'source_quality_status_counts': {'ok': 4382, 'pending_future_quotes': 3893}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `59` | `9.818787` | `2.88594` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 10, 'total_row_count': 64, 'entry_fill_rate': 0.15625, 'expired_rate': 0.3125, 'equal_weight_avg_final_return_pct': -0.491204, 'notional_weighted_ev_pct': -0.046754, 'source_quality_adjusted_ev_pct': -0.046754, 'diagnostic_win_rate': 0.3, 'downside_p10_pct': -3.609091, 'mae_p90_pct': -10.583329}`
- discovery_combined: `{'sample_count': 1014, 'source_quality_adjusted_ev_pct': -0.921549}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `400` | `0.779976` | `-9.094862` | `0.2975` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `295` | `-1.185746` | `-7.188498` | `0.186441` |
| `close_below_stop` | `329` | `-2.807129` | `-5.746814` | `0.109422` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `39` | `6.112679` | `-3.0` | `0.333333` |
| `neutral_location_observation` | `179` | `1.681541` | `-10.392157` | `0.396648` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `below_entry_recovery_observation` | `108` | `-0.825599` | `-9.642008` | `0.324074` |
| `pullback_retest_observation` | `295` | `-1.185746` | `-7.188498` | `0.186441` |
| `invalidation_observation` | `329` | `-2.807129` | `-5.746814` | `0.109422` |
| `discount_entry_observation` | `74` | `-3.0` | `-3.0` | `0.0` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `비철금속주` | `6` | `-11.828794` | `-11.828794` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `9` | `-8.884523` | `-14.796397` |
| `sector` | `Software Development and Supply` | `14` | `-7.108736` | `-12.067901` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `5` | `-6.920557` | `-10.883281` |
| `sector` | `Heavy Construction` | `7` | `-6.791581` | `-15.153027` |
| `theme_tags` | `SI(시스템통합)` | `5` | `-6.6293` | `-8.621132` |
| `theme_tags` | `중국_내수소비 확대,화장품` | `8` | `-6.321767` | `-8.932345` |
| `sector` | `Manufacture of Plastic Products` | `9` | `-5.721206` | `-15.588854` |
| `sector` | `Computer programming, System Integration and Management Services` | `19` | `-5.589835` | `-9.746438` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `19` | `-5.57421` | `-4.934893` |
| `theme_tags` | `미디어_디지털방송전환` | `5` | `-5.118469` | `-7.062419` |
| `theme_tags` | `의복_아웃도어` | `6` | `-5.095745` | `-11.624993` |
| `theme_tags` | `타이어` | `5` | `-4.706797` | `-7.45` |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `43` | `-4.631219` | `-7.184854` |
| `sector` | `Manufacture of Other Chemical Products` | `51` | `-4.614656` | `-13.589129` |
| `theme_tags` | `자동차_전장화 수혜` | `8` | `-4.484286` | `-6.341071` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `9` | `-4.461455` | `-5.117826` |
| `theme_tags` | `바이오_줄기세포치료제` | `5` | `-4.408262` | `-6.539874` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `5` | `-4.244531` | `-5.753846` |
| `sector` | `Manufacture of Electric Lamps and Bulbs` | `12` | `-4.106655` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
