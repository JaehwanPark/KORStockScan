# Swing Strategy Discovery EV - 2026-07-09

- generated_at: `2026-07-09T20:21:52`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1826` / `11712` / `11712`
- labeled_sample_count: `2164`
- pending_future_quote_count: `3654`
- bottom_rebound_policy_exit_row_count: `2160`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 1093, 'labeled': 450, 'expired_entry_no_trigger': 617}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 735, 'EXPIRED': 5894, 'EXITED': 2164, 'ENTERED': 2919}, 'label_status_counts': {'pending_future_quotes': 3654, 'expired_entry_no_trigger': 5894, 'labeled': 2164}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 1093, 'labeled': 450, 'expired_entry_no_trigger': 617}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 1093, 'matured_labeled': 450, 'matured_no_entry': 617}, 'bottom_rebound_pending_future_quote_count': 1093, 'bottom_rebound_labeled_sample_count': 450, 'bottom_rebound_expired_entry_count': 617, 'maturity_status_counts': {'pending_future_quotes': 3654, 'matured_no_entry': 5894, 'matured_labeled': 2164}, 'entry_reason_counts': {'breakout_not_touched': 2016, 'missing_next_quote': 400, 'gap_fade_condition_not_met': 1120, 'pullback_limit_touched': 1011, 'next_open': 2384, 'pullback_not_touched': 2565, 'breakout_trigger_touched': 368, 'bottom_rebound_signal_close_retest_touched': 438, 'bottom_rebound_atr_pullback_not_touched': 374, 'bottom_rebound_next_open': 592, 'gap_fade_limit_touched': 72, 'bottom_rebound_signal_close_retest_not_touched': 154, 'bottom_rebound_atr_pullback_touched': 218}, 'policy_exit_reason_counts': {'breakout_not_touched': 2016, 'missing_next_quote': 400, 'gap_fade_condition_not_met': 1120, 'need_10_quotes': 2548, 'need_5_quotes': 371, 'pullback_not_touched': 2565, 'fixed_5d_close': 893, 'fixed_10d_close': 598, 'trailing_after_mfe_stop': 85, 'mae_stop_touched': 584, 'scale_in_recovery_10d_close': 1, 'trailing_after_mfe_10d_close': 2, 'bottom_rebound_atr_pullback_not_touched': 374, 'bottom_rebound_signal_close_retest_not_touched': 154, 'mae_stop_time_stop_10d_close': 1}, 'source_quality_status_counts': {'pending_future_quotes': 3654, 'ok': 8058}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `87` | `16.974193` | `2.619973` | `0.977011` |
| `arm08_breakout_risk_mae_time` | `164` | `0.417132` | `-3.0` | `0.006098` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 18, 'total_row_count': 80, 'entry_fill_rate': 0.225, 'expired_rate': 0.45, 'equal_weight_avg_final_return_pct': -5.441886, 'notional_weighted_ev_pct': -5.670009, 'source_quality_adjusted_ev_pct': -5.670009, 'diagnostic_win_rate': 0.222222, 'downside_p10_pct': -18.776901, 'mae_p90_pct': -23.935736}`
- discovery_combined: `{'sample_count': 2146, 'source_quality_adjusted_ev_pct': -4.261808}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `no_touch` | `976` | `-1.90337` | `-17.694885` | `0.332992` |
| `wick_stop_recovered_close_above_stop` | `582` | `-3.87557` | `-18.364338` | `0.238832` |
| `close_below_stop` | `606` | `-8.505518` | `-21.835083` | `0.125413` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `108` | `16.789344` | `-12.975031` | `0.342593` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `307` | `-2.039327` | `-17.255956` | `0.384365` |
| `below_entry_recovery_observation` | `319` | `-3.517827` | `-16.299026` | `0.326019` |
| `pullback_retest_observation` | `582` | `-3.87557` | `-18.364338` | `0.238832` |
| `neutral_location_observation` | `232` | `-6.98828` | `-19.732254` | `0.275862` |
| `premium_entry_continuation_observation` | `10` | `-8.109327` | `-16.232497` | `0.2` |
| `invalidation_observation` | `606` | `-8.505518` | `-21.835083` | `0.125413` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Television Broadcasting` | `6` | `-18.806324` | `-18.0` |
| `sector` | `Manufacture of Man-Made Fibers` | `7` | `-17.424671` | `-22.830447` |
| `theme_tags` | `SI(시스템통합)` | `7` | `-17.064233` | `-23.845109` |
| `theme_tags` | `반도체_후공정장비` | `9` | `-16.894045` | `-29.518747` |
| `theme_tags` | `스마트폰_삼성전자관련주,휴대폰_베트남현지법인,휴대폰_카메라` | `7` | `-16.238163` | `-26.84492` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `13` | `-15.833806` | `-19.672695` |
| `theme_tags` | `PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주` | `10` | `-15.728403` | `-32.292672` |
| `theme_tags` | `원자력_설계시공` | `6` | `-15.509902` | `-22.671185` |
| `theme_tags` | `합성섬유_원료,합성수지` | `5` | `-15.135857` | `-16.295187` |
| `theme_tags` | `반도체_생산,반도체_시스템반도체` | `9` | `-14.561028` | `-26.556719` |
| `theme_tags` | `로봇_지능형` | `6` | `-14.240565` | `-14.261679` |
| `sector` | `Manufacture of Gas, Distribution of Gaseous Fuel Through Mains` | `5` | `-14.131898` | `-10.788998` |
| `sector` | `Computer programming, System Integration and Management Services` | `24` | `-13.98247` | `-23.01464` |
| `theme_tags` | `비철금속주` | `12` | `-13.931635` | `-18.579214` |
| `sector` | `Activities of Travel Agencies and Tour Operators and Tourist Assistance Activities` | `6` | `-13.593086` | `-20.50325` |
| `sector` | `Manufacture of Plastics and Synethetic Rubber in Primary forms` | `8` | `-13.335698` | `-14.237266` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `9` | `-13.285772` | `-23.752495` |
| `theme_tags` | `희소금속` | `12` | `-13.131181` | `-24.656846` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `29` | `-13.071072` | `-20.124728` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `14` | `-12.725022` | `-31.195181` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
