# Swing Strategy Discovery EV - 2026-06-09

- generated_at: `2026-06-09T16:05:52`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `298` / `1903` / `1903`
- labeled_sample_count: `187`
- pending_future_quote_count: `1601`
- bottom_rebound_policy_exit_row_count: `327`
- bottom_rebound_label_status_counts: `{'labeled': 55, 'pending_future_quotes': 270, 'expired_entry_no_trigger': 2}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'EXITED': 187, 'ENTERED': 635, 'PENDING_ENTRY': 966, 'EXPIRED': 115}, 'label_status_counts': {'pending_future_quotes': 1601, 'labeled': 187, 'expired_entry_no_trigger': 115}, 'bottom_rebound_label_status_counts': {'labeled': 55, 'pending_future_quotes': 270, 'expired_entry_no_trigger': 2}, 'bottom_rebound_maturity_status_counts': {'matured_labeled': 55, 'pending_future_quotes': 270, 'matured_no_entry': 2}, 'bottom_rebound_pending_future_quote_count': 270, 'bottom_rebound_labeled_sample_count': 55, 'bottom_rebound_expired_entry_count': 2, 'maturity_status_counts': {'pending_future_quotes': 1601, 'matured_labeled': 187, 'matured_no_entry': 115}, 'entry_reason_counts': {'missing_next_quote': 741, 'bottom_rebound_atr_pullback_touched': 62, 'bottom_rebound_signal_close_retest_touched': 62, 'bottom_rebound_next_open': 62, 'pullback_limit_touched': 351, 'breakout_not_touched': 210, 'next_open': 244, 'gap_fade_condition_not_met': 115, 'breakout_trigger_touched': 34, 'gap_fade_limit_touched': 7, 'pullback_not_touched': 15}, 'policy_exit_reason_counts': {'missing_next_quote': 741, 'mae_stop_touched': 179, 'need_10_quotes': 506, 'breakout_not_touched': 210, 'need_5_quotes': 129, 'gap_fade_condition_not_met': 115, 'trailing_after_mfe_stop': 8, 'pullback_not_touched': 15}, 'source_quality_status_counts': {'pending_future_quotes': 1601, 'ok': 302}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `8` | `9.479507` | `3.547541` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 3, 'total_row_count': 24, 'entry_fill_rate': 0.125, 'expired_rate': 0.125, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.8, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -17.664248}`
- discovery_combined: `{'sample_count': 184, 'source_quality_adjusted_ev_pct': -1.96918}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `1` | `4.840006` | `24.200029` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `41` | `-1.364588` | `-3.0` | `0.097561` |
| `close_below_stop` | `145` | `-2.606558` | `-3.0` | `0.02069` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `1` | `4.840006` | `24.200029` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `below_entry_recovery_observation` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `41` | `-1.364588` | `-3.0` | `0.097561` |
| `invalidation_observation` | `145` | `-2.606558` | `-3.0` | `0.02069` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `block_reason` | `blocked_swing_score_vpw` | `9` | `-3.0` | `-3.0` |
| `block_reason` | `blocked_swing_gap` | `6` | `-3.0` | `-3.0` |
| `block_reason` | `blocked_gatekeeper_reject` | `5` | `-3.0` | `-3.0` |
| `sector` | `Other Financial Intermediation` | `27` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `12` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `5` | `-3.0` | `-3.0` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `5` | `-3.0` | `-3.0` |
| `sector` | `Data Processing, Hosting and Related activities; Web Portals` | `5` | `-3.0` | `-3.0` |
| `sector` | `Architectural, Engineering and Related Technical Services` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Chemicals` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `5` | `-3.0` | `-3.0` |
| `position_tag` | `MIDDLE` | `27` | `-2.699962` | `-3.0` |
| `theme_tags` | `NaN` | `25` | `-2.518738` | `-3.0` |
| `sector` | `Manufacture of Electronic Components` | `17` | `-2.398446` | `-3.0` |
| `theme_tags` | `-` | `75` | `-2.277071` | `-3.0` |
| `position_tag` | `nan` | `45` | `-2.212275` | `-3.0` |
| `volatility_bucket` | `low` | `187` | `-2.022181` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
