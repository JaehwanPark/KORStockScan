# Swing Strategy Discovery EV - 2026-06-26

- generated_at: `2026-06-26T21:32:10`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1338` / `8675` / `8675`
- labeled_sample_count: `1008`
- pending_future_quote_count: `4242`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 913, 'expired_entry_no_trigger': 383, 'labeled': 139}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXPIRED': 3425, 'PENDING_ENTRY': 1234, 'ENTERED': 3008, 'EXITED': 1008}, 'label_status_counts': {'expired_entry_no_trigger': 3425, 'pending_future_quotes': 4242, 'labeled': 1008}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 913, 'expired_entry_no_trigger': 383, 'labeled': 139}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 913, 'matured_no_entry': 383, 'matured_labeled': 139}, 'bottom_rebound_pending_future_quote_count': 913, 'bottom_rebound_labeled_sample_count': 139, 'bottom_rebound_expired_entry_count': 383, 'maturity_status_counts': {'matured_no_entry': 3425, 'pending_future_quotes': 4242, 'matured_labeled': 1008}, 'entry_reason_counts': {'breakout_not_touched': 1378, 'gap_fade_condition_not_met': 764, 'pullback_not_touched': 1386, 'missing_next_quote': 800, 'gap_fade_limit_touched': 58, 'breakout_trigger_touched': 266, 'next_open': 1644, 'pullback_limit_touched': 1080, 'bottom_rebound_next_open': 433, 'bottom_rebound_atr_pullback_not_touched': 247, 'bottom_rebound_signal_close_retest_touched': 349, 'bottom_rebound_signal_close_retest_not_touched': 84, 'bottom_rebound_atr_pullback_touched': 186}, 'policy_exit_reason_counts': {'breakout_not_touched': 1378, 'gap_fade_condition_not_met': 764, 'pullback_not_touched': 1386, 'missing_next_quote': 800, 'fixed_5d_close': 416, 'mae_stop_touched': 524, 'trailing_after_mfe_stop': 68, 'need_10_quotes': 2544, 'bottom_rebound_atr_pullback_not_touched': 247, 'bottom_rebound_signal_close_retest_not_touched': 84, 'need_5_quotes': 464}, 'source_quality_status_counts': {'ok': 4433, 'pending_future_quotes': 4242}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `68` | `7.344213` | `2.550987` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 13, 'total_row_count': 64, 'entry_fill_rate': 0.203125, 'expired_rate': 0.28125, 'equal_weight_avg_final_return_pct': -3.554009, 'notional_weighted_ev_pct': -3.500039, 'source_quality_adjusted_ev_pct': -3.500039, 'diagnostic_win_rate': 0.153846, 'downside_p10_pct': -5.973134, 'mae_p90_pct': -17.087859}`
- discovery_combined: `{'sample_count': 995, 'source_quality_adjusted_ev_pct': -2.181029}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `229` | `-0.791432` | `-10.715848` | `0.270742` |
| `no_touch` | `403` | `-2.251057` | `-12.343902` | `0.280397` |
| `close_below_stop` | `376` | `-3.200556` | `-3.188389` | `0.106383` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `premium_entry_continuation_observation` | `6` | `1.590585` | `-3.0` | `0.666667` |
| `momentum_chase_observation` | `33` | `0.550784` | `-3.0` | `0.212121` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `229` | `-0.791432` | `-10.715848` | `0.270742` |
| `neutral_location_observation` | `184` | `-2.261743` | `-15.609815` | `0.288043` |
| `below_entry_recovery_observation` | `152` | `-2.762057` | `-11.252721` | `0.322368` |
| `discount_entry_observation` | `28` | `-3.0` | `-3.0` | `0.0` |
| `invalidation_observation` | `376` | `-3.200556` | `-3.188389` | `0.106383` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Audio Publishing and Original Master Recordings` | `6` | `-12.829398` | `-18.56833` |
| `sector` | `Manufacture of Man-Made Fibers` | `5` | `-12.55812` | `-18.783069` |
| `theme_tags` | `태양광_폴리실리콘` | `5` | `-12.518898` | `-29.114831` |
| `theme_tags` | `의복_아웃도어` | `6` | `-11.777502` | `-18.783069` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `10` | `-9.959444` | `-19.978939` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `17` | `-9.901718` | `-12.205372` |
| `sector` | `Telecommunications` | `6` | `-8.735738` | `-13.023298` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `9` | `-8.553015` | `-23.647146` |
| `theme_tags` | `미디어_디지털방송전환` | `5` | `-8.46219` | `-13.201783` |
| `theme_tags` | `LCD_부품,반도체_설계(fabless),반도체_시스템반도체,스마트폰_애플 관련주` | `5` | `-8.330637` | `-14.638887` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `7` | `-8.076067` | `-12.934706` |
| `sector` | `Computer programming, System Integration and Management Services` | `17` | `-7.765136` | `-21.356554` |
| `sector` | `Manufacture of Plastic Products` | `10` | `-7.516041` | `-17.065463` |
| `theme_tags` | `증권,창투` | `5` | `-7.01004` | `-13.184584` |
| `theme_tags` | `중국_내수소비 확대,화장품` | `6` | `-6.849722` | `-10.283824` |
| `sector` | `Software Development and Supply` | `16` | `-6.154578` | `-13.338356` |
| `theme_tags` | `바이오_줄기세포치료제` | `5` | `-6.063538` | `-10.700657` |
| `sector` | `Manufacture of Other Chemical Products` | `51` | `-5.630569` | `-14.147627` |
| `theme_tags` | `원자력_기자재,화력_발전기자재` | `6` | `-5.314209` | `-14.049537` |
| `block_reason` | `blocked_gatekeeper_reject` | `83` | `-5.27518` | `-16.495548` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
