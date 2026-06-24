# Swing Strategy Discovery EV - 2026-06-24

- generated_at: `2026-06-24T20:22:11`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `1238` / `7875` / `7875`
- labeled_sample_count: `1209`
- pending_future_quote_count: `4072`
- bottom_rebound_policy_exit_row_count: `1435`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 900, 'expired_entry_no_trigger': 308, 'labeled': 227}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 868, 'ENTERED': 3204, 'EXPIRED': 2594, 'EXITED': 1209}, 'label_status_counts': {'pending_future_quotes': 4072, 'labeled': 1209, 'expired_entry_no_trigger': 2594}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 900, 'expired_entry_no_trigger': 308, 'labeled': 227}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 900, 'matured_no_entry': 308, 'matured_labeled': 227}, 'bottom_rebound_pending_future_quote_count': 900, 'bottom_rebound_labeled_sample_count': 227, 'bottom_rebound_expired_entry_count': 308, 'maturity_status_counts': {'pending_future_quotes': 4072, 'matured_labeled': 1209, 'matured_no_entry': 2594}, 'entry_reason_counts': {'breakout_not_touched': 1122, 'missing_next_quote': 488, 'pullback_limit_touched': 1386, 'gap_fade_condition_not_met': 695, 'next_open': 1522, 'bottom_rebound_next_open': 433, 'gap_fade_limit_touched': 66, 'pullback_not_touched': 897, 'breakout_trigger_touched': 400, 'bottom_rebound_atr_pullback_not_touched': 192, 'bottom_rebound_signal_close_retest_touched': 365, 'bottom_rebound_signal_close_retest_not_touched': 68, 'bottom_rebound_atr_pullback_touched': 241}, 'policy_exit_reason_counts': {'breakout_not_touched': 1122, 'missing_next_quote': 488, 'mae_stop_touched': 799, 'gap_fade_condition_not_met': 695, 'need_10_quotes': 2666, 'need_5_quotes': 538, 'fixed_5d_close': 289, 'pullback_not_touched': 897, 'trailing_after_mfe_stop': 121, 'bottom_rebound_atr_pullback_not_touched': 192, 'bottom_rebound_signal_close_retest_not_touched': 68}, 'source_quality_status_counts': {'pending_future_quotes': 4072, 'ok': 3803}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `121` | `7.281372` | `2.461471` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 16, 'total_row_count': 64, 'entry_fill_rate': 0.25, 'expired_rate': 0.25, 'equal_weight_avg_final_return_pct': -2.316267, 'notional_weighted_ev_pct': -2.214296, 'source_quality_adjusted_ev_pct': -2.214296, 'diagnostic_win_rate': 0.1875, 'downside_p10_pct': -4.858209, 'mae_p90_pct': -14.676901}`
- discovery_combined: `{'sample_count': 1193, 'source_quality_adjusted_ev_pct': -0.386551}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `433` | `0.608385` | `-3.787476` | `0.26097` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `354` | `-0.158289` | `-4.208505` | `0.262712` |
| `close_below_stop` | `422` | `-1.838554` | `-3.0` | `0.123223` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `neutral_location_observation` | `35` | `3.105225` | `-3.0` | `0.4` |
| `momentum_chase_observation` | `94` | `2.30877` | `-3.0` | `0.255319` |
| `discount_entry_observation` | `111` | `1.419934` | `-4.086538` | `0.243243` |
| `premium_entry_continuation_observation` | `1` | `1.360544` | `6.802721` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `354` | `-0.158289` | `-4.208505` | `0.262712` |
| `below_entry_recovery_observation` | `192` | `-1.104312` | `-4.835905` | `0.244792` |
| `invalidation_observation` | `422` | `-1.838554` | `-3.0` | `0.123223` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `theme_tags` | `비철금속주` | `6` | `-12.587744` | `-12.587744` |
| `sector` | `Computer programming, System Integration and Management Services` | `20` | `-7.224913` | `-21.356554` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `18` | `-7.024715` | `-9.193756` |
| `theme_tags` | `SNS(Social Network Service),게임_모바일` | `13` | `-6.740252` | `-10.982129` |
| `sector` | `Manufacture of Motor Vehicles and Engines for Motor Vehicles` | `8` | `-5.405393` | `-9.4919` |
| `sector` | `Telecommunications` | `5` | `-4.943213` | `-7.770506` |
| `sector` | `Retail Sale of Fuel` | `8` | `-4.151613` | `-6.378774` |
| `sector` | `Software Development and Supply` | `14` | `-3.9144` | `-8.951407` |
| `sector` | `Manufacture of Plastic Products` | `11` | `-3.528582` | `-4.086538` |
| `sector` | `Data Processing, Hosting and Related activities; Web Portals` | `20` | `-3.493416` | `-8.203183` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `30` | `-3.477939` | `-5.723654` |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `52` | `-3.230706` | `-4.808649` |
| `theme_tags` | `그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체` | `11` | `-3.212889` | `-3.0` |
| `sector` | `Research and Experimental Development On Natural Sciences and Engineering` | `7` | `-3.205196` | `-3.294118` |
| `theme_tags` | `중국_내수소비 확대,화장품` | `8` | `-3.159115` | `-4.026007` |
| `sector` | `Manufacture of primary battery and secondary battery` | `19` | `-3.124348` | `-3.97878` |
| `block_reason` | `blocked_gatekeeper_reject` | `86` | `-3.033343` | `-7.009542` |
| `theme_tags` | `기계_건설기계` | `5` | `-3.0` | `-5.607004` |
| `sector` | `Road Freight Transport` | `12` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of medicinal chemicals` | `7` | `-3.0` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
