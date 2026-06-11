# Swing Strategy Discovery EV - 2026-06-11

- generated_at: `2026-06-11T16:06:51`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `492` / `3146` / `3146`
- labeled_sample_count: `284`
- pending_future_quote_count: `2655`
- bottom_rebound_policy_exit_row_count: `538`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 486, 'labeled': 48, 'expired_entry_no_trigger': 4}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 1223, 'EXITED': 284, 'PENDING_ENTRY': 1432, 'EXPIRED': 207}, 'label_status_counts': {'pending_future_quotes': 2655, 'labeled': 284, 'expired_entry_no_trigger': 207}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 486, 'labeled': 48, 'expired_entry_no_trigger': 4}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 486, 'matured_labeled': 48, 'matured_no_entry': 4}, 'bottom_rebound_pending_future_quote_count': 486, 'bottom_rebound_labeled_sample_count': 48, 'bottom_rebound_expired_entry_count': 4, 'maturity_status_counts': {'pending_future_quotes': 2655, 'matured_labeled': 284, 'matured_no_entry': 207}, 'entry_reason_counts': {'pullback_limit_touched': 552, 'pullback_not_touched': 114, 'breakout_trigger_touched': 180, 'gap_fade_condition_not_met': 207, 'breakout_not_touched': 264, 'bottom_rebound_next_open': 128, 'bottom_rebound_signal_close_retest_touched': 100, 'bottom_rebound_atr_pullback_touched': 88, 'bottom_rebound_signal_close_retest_not_touched': 28, 'bottom_rebound_atr_pullback_not_touched': 40, 'next_open': 444, 'gap_fade_limit_touched': 15, 'missing_next_quote': 986}, 'policy_exit_reason_counts': {'need_10_quotes': 986, 'mae_stop_touched': 248, 'pullback_not_touched': 114, 'gap_fade_condition_not_met': 207, 'breakout_not_touched': 264, 'bottom_rebound_signal_close_retest_not_touched': 28, 'bottom_rebound_atr_pullback_not_touched': 40, 'need_5_quotes': 237, 'trailing_after_mfe_stop': 36, 'missing_next_quote': 986}, 'source_quality_status_counts': {'pending_future_quotes': 2655, 'ok': 491}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `36` | `8.060221` | `2.479264` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 3, 'total_row_count': 24, 'entry_fill_rate': 0.125, 'expired_rate': 0.125, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.8, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -15.137467}`
- discovery_combined: `{'sample_count': 281, 'source_quality_adjusted_ev_pct': -0.925859}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `17` | `9.764386` | `0.167621` | `0.882353` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `103` | `-1.213879` | `-3.0` | `0.135922` |
| `close_below_stop` | `164` | `-2.380938` | `-3.0` | `0.042683` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `10` | `9.917975` | `3.122977` | `1.0` |
| `below_entry_recovery_observation` | `5` | `9.445932` | `2.723816` | `1.0` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `1` | `-0.6` | `-3.0` | `0.0` |
| `discount_entry_observation` | `1` | `-0.6` | `-3.0` | `0.0` |
| `pullback_retest_observation` | `103` | `-1.213879` | `-3.0` | `0.135922` |
| `invalidation_observation` | `164` | `-2.380938` | `-3.0` | `0.042683` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `block_reason` | `blocked_swing_gap` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `10` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `9` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Chemicals` | `7` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `7` | `-3.0` | `-3.0` |
| `sector` | `Data Processing, Hosting and Related activities; Web Portals` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `반도체_생산` | `8` | `-3.0` | `-3.0` |
| `sector` | `Other Financial Intermediation` | `37` | `-2.380574` | `-3.0` |
| `block_reason` | `blocked_swing_score_vpw` | `14` | `-2.378086` | `-3.0` |
| `sector` | `Manufacture of Electronic Components` | `34` | `-2.28352` | `-3.0` |
| `position_tag` | `MIDDLE` | `51` | `-1.98118` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `9` | `-1.808469` | `-3.0` |
| `position_tag` | `nan` | `80` | `-1.326547` | `-3.0` |
| `theme_tags` | `-` | `115` | `-1.222447` | `-3.0` |
| `sector` | `Insurance` | `10` | `-1.113544` | `-3.0` |
| `block_reason` | `blocked_gatekeeper_reject` | `16` | `-1.096236` | `-3.0` |
| `sector` | `Software Development and Supply` | `6` | `-1.047507` | `-3.0` |
| `theme_tags` | `NaN` | `42` | `-0.974821` | `-3.0` |
| `volatility_bucket` | `low` | `284` | `-0.958839` | `-3.0` |
| `block_reason` | `no_block_observed` | `249` | `-0.823292` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
