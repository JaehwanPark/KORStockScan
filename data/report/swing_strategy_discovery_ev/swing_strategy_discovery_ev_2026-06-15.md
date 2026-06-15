# Swing Strategy Discovery EV - 2026-06-15

- generated_at: `2026-06-15T16:12:20`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `677` / `4310` / `4310`
- labeled_sample_count: `377`
- pending_future_quote_count: `3425`
- bottom_rebound_policy_exit_row_count: `766`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 719, 'expired_entry_no_trigger': 18, 'labeled': 29}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `15`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 1715, 'EXITED': 377, 'PENDING_ENTRY': 1710, 'EXPIRED': 508}, 'label_status_counts': {'pending_future_quotes': 3425, 'labeled': 377, 'expired_entry_no_trigger': 508}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 719, 'expired_entry_no_trigger': 18, 'labeled': 29}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 719, 'matured_no_entry': 18, 'matured_labeled': 29}, 'bottom_rebound_pending_future_quote_count': 719, 'bottom_rebound_labeled_sample_count': 29, 'bottom_rebound_expired_entry_count': 18, 'maturity_status_counts': {'pending_future_quotes': 3425, 'matured_labeled': 377, 'matured_no_entry': 508}, 'entry_reason_counts': {'pullback_limit_touched': 537, 'breakout_not_touched': 208, 'gap_fade_condition_not_met': 306, 'pullback_not_touched': 477, 'bottom_rebound_signal_close_retest_touched': 109, 'bottom_rebound_atr_pullback_not_touched': 134, 'bottom_rebound_next_open': 202, 'bottom_rebound_signal_close_retest_not_touched': 93, 'bottom_rebound_atr_pullback_touched': 68, 'next_open': 676, 'breakout_trigger_touched': 468, 'gap_fade_limit_touched': 32, 'missing_next_quote': 1000}, 'policy_exit_reason_counts': {'need_10_quotes': 1345, 'mae_stop_touched': 233, 'breakout_not_touched': 208, 'gap_fade_condition_not_met': 306, 'pullback_not_touched': 477, 'bottom_rebound_atr_pullback_not_touched': 134, 'bottom_rebound_signal_close_retest_not_touched': 93, 'need_5_quotes': 370, 'trailing_after_mfe_stop': 144, 'missing_next_quote': 1000}, 'source_quality_status_counts': {'pending_future_quotes': 3425, 'ok': 885}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `144` | `7.927725` | `2.41638` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 2, 'total_row_count': 24, 'entry_fill_rate': 0.083333, 'expired_rate': 0.375, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.2, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -12.734982}`
- discovery_combined: `{'sample_count': 375, 'source_quality_adjusted_ev_pct': 2.031228}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `109` | `7.272596` | `2.028106` | `0.908257` |
| `wick_stop_recovered_close_above_stop` | `158` | `0.29095` | `-3.0` | `0.221519` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `close_below_stop` | `110` | `-1.979344` | `-3.0` | `0.090909` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `59` | `9.05577` | `2.693956` | `1.0` |
| `neutral_location_observation` | `13` | `6.96385` | `-3.0` | `0.538462` |
| `below_entry_recovery_observation` | `31` | `4.831877` | `2.035433` | `0.935484` |
| `premium_entry_continuation_observation` | `4` | `3.437074` | `2.768262` | `1.0` |
| `pullback_retest_observation` | `158` | `0.29095` | `-3.0` | `0.221519` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `2` | `-1.2` | `-3.0` | `0.0` |
| `invalidation_observation` | `110` | `-1.979344` | `-3.0` | `0.090909` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `10` | `-3.0` | `-3.0` |
| `sector` | `-` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `반도체_생산` | `9` | `-3.0` | `-3.0` |
| `theme_tags` | `그린카_하이브리드카/전기차` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `보험_손해보험` | `7` | `-2.082198` | `-3.0` |
| `sector` | `Software Development and Supply` | `6` | `-1.733531` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `12` | `-1.641392` | `-3.0` |
| `block_reason` | `blocked_swing_gap` | `6` | `-1.480517` | `-3.0` |
| `sector` | `Computer programming, System Integration and Management Services` | `6` | `-1.387088` | `-3.0` |
| `sector` | `Sea and Coastal Water Transport` | `7` | `-0.643888` | `-3.0` |
| `theme_tags` | `운송_해운` | `7` | `-0.643888` | `-3.0` |
| `theme_tags` | `PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라` | `5` | `-0.559602` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `11` | `-0.544086` | `-3.0` |
| `sector` | `Activities Auxiliary to Financial Service Activities` | `6` | `-0.28906` | `-3.0` |
| `theme_tags` | `증권` | `6` | `-0.28906` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
