# Swing Strategy Discovery EV - 2026-06-18

- generated_at: `2026-06-18T16:10:45`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `954` / `6083` / `6083`
- labeled_sample_count: `546`
- pending_future_quote_count: `4237`
- bottom_rebound_policy_exit_row_count: `1083`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 889, 'expired_entry_no_trigger': 181, 'labeled': 13}`
- top_surviving_arm: `arm06_gap_fade_risk_fixed5d`
- avoid_bucket_count: `15`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1771, 'EXPIRED': 1300, 'ENTERED': 2466, 'EXITED': 546}, 'label_status_counts': {'pending_future_quotes': 4237, 'expired_entry_no_trigger': 1300, 'labeled': 546}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 889, 'expired_entry_no_trigger': 181, 'labeled': 13}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 889, 'matured_no_entry': 181, 'matured_labeled': 13}, 'bottom_rebound_pending_future_quote_count': 889, 'bottom_rebound_labeled_sample_count': 13, 'bottom_rebound_expired_entry_count': 181, 'maturity_status_counts': {'pending_future_quotes': 4237, 'matured_no_entry': 1300, 'matured_labeled': 546}, 'entry_reason_counts': {'pullback_not_touched': 900, 'breakout_not_touched': 404, 'gap_fade_condition_not_met': 482, 'next_open': 1060, 'bottom_rebound_next_open': 291, 'bottom_rebound_signal_close_retest_touched': 195, 'bottom_rebound_atr_pullback_not_touched': 219, 'bottom_rebound_atr_pullback_touched': 72, 'pullback_limit_touched': 690, 'breakout_trigger_touched': 656, 'gap_fade_limit_touched': 48, 'bottom_rebound_signal_close_retest_not_touched': 96, 'missing_next_quote': 970}, 'policy_exit_reason_counts': {'pullback_not_touched': 900, 'breakout_not_touched': 404, 'gap_fade_condition_not_met': 482, 'need_10_quotes': 1953, 'bottom_rebound_atr_pullback_not_touched': 219, 'need_5_quotes': 513, 'fixed_5d_close': 65, 'trailing_after_mfe_stop': 191, 'mae_stop_touched': 290, 'bottom_rebound_signal_close_retest_not_touched': 96, 'missing_next_quote': 970}, 'source_quality_status_counts': {'pending_future_quotes': 4237, 'ok': 1846}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm06_gap_fade_risk_fixed5d` | `5` | `20.914529` | `1.81619` | `0.8` |
| `arm05_breakout_conf_trailing` | `191` | `8.329584` | `2.613699` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 4, 'total_row_count': 24, 'entry_fill_rate': 0.166667, 'expired_rate': 0.375, 'equal_weight_avg_final_return_pct': -9.00898, 'notional_weighted_ev_pct': -9.410167, 'source_quality_adjusted_ev_pct': -7.528133, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -18.338577, 'mae_p90_pct': -24.103548}`
- discovery_combined: `{'sample_count': 542, 'source_quality_adjusted_ev_pct': 2.641053}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `204` | `5.73967` | `-3.0` | `0.70098` |
| `wick_stop_recovered_close_above_stop` | `250` | `0.818016` | `-3.0` | `0.28` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `92` | `-0.200115` | `-3.0` | `0.217391` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `115` | `7.808025` | `-3.0` | `0.834783` |
| `discount_entry_observation` | `7` | `5.505752` | `-3.0` | `0.142857` |
| `below_entry_recovery_observation` | `47` | `3.494503` | `-3.0` | `0.595745` |
| `premium_entry_continuation_observation` | `4` | `2.305015` | `-1.446387` | `0.75` |
| `neutral_location_observation` | `31` | `1.360278` | `-3.0` | `0.483871` |
| `pullback_retest_observation` | `250` | `0.818016` | `-3.0` | `0.28` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `92` | `-0.200115` | `-3.0` | `0.217391` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Computer programming, System Integration and Management Services` | `10` | `-5.963511` | `-9.95006` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `16` | `-4.648384` | `-3.0` |
| `sector` | `Telecommunications` | `5` | `-4.445573` | `-6.903839` |
| `theme_tags` | `반도체_생산` | `12` | `-2.100143` | `-3.0` |
| `theme_tags` | `자원개발 E&P` | `9` | `-1.89704` | `-4.208511` |
| `sector` | `Activities Auxiliary to Financial Service Activities` | `12` | `-1.766246` | `-3.0` |
| `theme_tags` | `PCB(인쇄회로기판)` | `5` | `-1.734002` | `-3.0` |
| `theme_tags` | `증권` | `11` | `-1.656718` | `-3.0` |
| `sector` | `Manufacture of primary battery and secondary battery` | `7` | `-0.659282` | `-3.0` |
| `sector` | `Software Development and Supply` | `6` | `-0.631203` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `9` | `-0.622748` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `18` | `-0.382225` | `-3.0` |
| `block_reason` | `blocked_gatekeeper_reject` | `59` | `-0.227789` | `-3.0` |
| `sector` | `Audio Publishing and Original Master Recordings` | `5` | `-0.07711` | `-3.0` |
| `theme_tags` | `그린카_하이브리드카/전기차` | `7` | `7.807152` | `-6.02576` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
