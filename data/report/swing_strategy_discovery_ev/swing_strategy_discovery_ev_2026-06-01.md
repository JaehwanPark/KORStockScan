# Swing Strategy Discovery EV - 2026-06-01

- generated_at: `2026-06-01T22:35:58`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `634` / `4525` / `4525`
- labeled_sample_count: `315`
- pending_future_quote_count: `3212`
- bottom_rebound_policy_exit_row_count: `511`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 458, 'labeled': 42, 'expired_entry_no_trigger': 11}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `11`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1355, 'EXPIRED': 998, 'ENTERED': 1857, 'EXITED': 315}, 'label_status_counts': {'pending_future_quotes': 3212, 'expired_entry_no_trigger': 998, 'labeled': 315}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 458, 'labeled': 42, 'expired_entry_no_trigger': 11}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 458, 'matured_labeled': 42, 'matured_no_entry': 11}, 'bottom_rebound_pending_future_quote_count': 458, 'bottom_rebound_labeled_sample_count': 42, 'bottom_rebound_expired_entry_count': 11, 'maturity_status_counts': {'pending_future_quotes': 3212, 'matured_no_entry': 998, 'matured_labeled': 315}, 'entry_reason_counts': {'missing_next_quote': 571, 'gap_fade_condition_not_met': 439, 'bottom_rebound_next_open': 102, 'next_open': 912, 'pullback_not_touched': 693, 'breakout_not_touched': 632, 'bottom_rebound_signal_close_retest_touched': 98, 'breakout_trigger_touched': 280, 'pullback_limit_touched': 675, 'bottom_rebound_atr_pullback_touched': 88, 'gap_fade_limit_touched': 17, 'bottom_rebound_atr_pullback_not_touched': 14, 'bottom_rebound_signal_close_retest_not_touched': 4}, 'policy_exit_reason_counts': {'missing_next_quote': 571, 'gap_fade_condition_not_met': 439, 'need_10_quotes': 1384, 'need_5_quotes': 473, 'pullback_not_touched': 693, 'breakout_not_touched': 632, 'trailing_after_mfe_stop': 86, 'mae_stop_touched': 229, 'bottom_rebound_atr_pullback_not_touched': 14, 'bottom_rebound_signal_close_retest_not_touched': 4}, 'source_quality_status_counts': {'pending_future_quotes': 3212, 'ok': 1313}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `86` | `17.090802` | `3.972268` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 1, 'total_row_count': 40, 'entry_fill_rate': 0.025, 'expired_rate': 0.075, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -0.6, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -3.598486}`
- discovery_combined: `{'sample_count': 314, 'source_quality_adjusted_ev_pct': 3.955864}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `53` | `22.37967` | `4.816146` | `0.962264` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `167` | `-0.545169` | `-3.0` | `0.173653` |
| `close_below_stop` | `95` | `-2.257107` | `-3.0` | `0.063158` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `34` | `30.555138` | `9.957304` | `0.970588` |
| `below_entry_recovery_observation` | `17` | `7.130901` | `3.498624` | `0.941176` |
| `premium_entry_continuation_observation` | `2` | `3.106021` | `7.693104` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `167` | `-0.545169` | `-3.0` | `0.173653` |
| `invalidation_observation` | `95` | `-2.257107` | `-3.0` | `0.063158` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `12` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Chemicals` | `11` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `10` | `-3.0` | `-3.0` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `10` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `7` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Plastic Products` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `22` | `-2.231644` | `-3.0` |
| `position_tag` | `BOTTOM` | `90` | `-2.090892` | `-3.0` |
| `theme_tags` | `휴대폰_수동부품` | `6` | `-1.934809` | `-3.0` |
| `sector` | `Manufacture of Electric Motors, Generators and Transforming, Distributing and Controlling Apparatus of Electricity` | `11` | `-0.119129` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
