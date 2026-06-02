# Swing Strategy Discovery EV - 2026-06-02

- generated_at: `2026-06-02T16:18:21`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `684` / `4925` / `4925`
- labeled_sample_count: `232`
- pending_future_quote_count: `3634`
- bottom_rebound_policy_exit_row_count: `511`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 474, 'labeled': 25, 'expired_entry_no_trigger': 12}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `9`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1963, 'EXITED': 232, 'ENTERED': 1671, 'EXPIRED': 1059}, 'label_status_counts': {'pending_future_quotes': 3634, 'labeled': 232, 'expired_entry_no_trigger': 1059}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 474, 'labeled': 25, 'expired_entry_no_trigger': 12}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 474, 'matured_labeled': 25, 'matured_no_entry': 12}, 'bottom_rebound_pending_future_quote_count': 474, 'bottom_rebound_labeled_sample_count': 25, 'bottom_rebound_expired_entry_count': 12, 'maturity_status_counts': {'pending_future_quotes': 3634, 'matured_labeled': 232, 'matured_no_entry': 1059}, 'entry_reason_counts': {'pullback_not_touched': 894, 'breakout_trigger_touched': 222, 'next_open': 912, 'breakout_not_touched': 690, 'gap_fade_condition_not_met': 441, 'bottom_rebound_signal_close_retest_touched': 98, 'bottom_rebound_atr_pullback_not_touched': 22, 'bottom_rebound_next_open': 102, 'bottom_rebound_atr_pullback_touched': 80, 'pullback_limit_touched': 474, 'gap_fade_limit_touched': 15, 'bottom_rebound_signal_close_retest_not_touched': 4, 'missing_next_quote': 971}, 'policy_exit_reason_counts': {'pullback_not_touched': 894, 'trailing_after_mfe_stop': 79, 'need_5_quotes': 471, 'breakout_not_touched': 690, 'gap_fade_condition_not_met': 441, 'need_10_quotes': 1200, 'bottom_rebound_atr_pullback_not_touched': 22, 'mae_stop_touched': 153, 'bottom_rebound_signal_close_retest_not_touched': 4, 'missing_next_quote': 971}, 'source_quality_status_counts': {'pending_future_quotes': 3634, 'ok': 1291}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `79` | `16.543844` | `3.187241` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 0, 'total_row_count': 40, 'entry_fill_rate': 0.0, 'expired_rate': 0.075, 'equal_weight_avg_final_return_pct': 0.0, 'notional_weighted_ev_pct': 0.0, 'source_quality_adjusted_ev_pct': 0.0, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': None, 'mae_p90_pct': None}`
- discovery_combined: `{'sample_count': 232, 'source_quality_adjusted_ev_pct': 5.071056}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `37` | `26.807044` | `7.117635` | `0.972973` |
| `wick_stop_recovered_close_above_stop` | `136` | `0.440485` | `-3.0` | `0.264706` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `59` | `-1.909224` | `-3.0` | `0.118644` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `30` | `31.647107` | `16.332661` | `1.0` |
| `below_entry_recovery_observation` | `7` | `5.65438` | `2.450305` | `0.857143` |
| `pullback_retest_observation` | `136` | `0.440485` | `-3.0` | `0.264706` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `invalidation_observation` | `59` | `-1.909224` | `-3.0` | `0.118644` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Basic Chemicals` | `9` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `7` | `-3.0` | `-3.0` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Parts and Accessories for Motor Vehicles(New Products)` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `휴대폰_수동부품` | `5` | `-3.0` | `-3.0` |
| `position_tag` | `BOTTOM` | `49` | `-1.896336` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `13` | `-1.74559` | `-3.0` |
| `sector` | `Insurance` | `9` | `-0.309067` | `-3.0` |
| `theme_tags` | `보험_생명보험` | `8` | `-0.042818` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
