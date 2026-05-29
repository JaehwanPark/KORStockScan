# Swing Strategy Discovery EV - 2026-05-28

- generated_at: `2026-05-29T11:14:34`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `406` / `3102` / `3102`
- labeled_sample_count: `261`
- pending_future_quote_count: `2457`
- bottom_rebound_policy_exit_row_count: `126`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 107, 'labeled': 16, 'expired_entry_no_trigger': 3}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1139, 'EXPIRED': 384, 'EXITED': 261, 'ENTERED': 1318}, 'label_status_counts': {'pending_future_quotes': 2457, 'expired_entry_no_trigger': 384, 'labeled': 261}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 107, 'labeled': 16, 'expired_entry_no_trigger': 3}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 107, 'matured_labeled': 16, 'matured_no_entry': 3}, 'bottom_rebound_pending_future_quote_count': 107, 'bottom_rebound_labeled_sample_count': 16, 'bottom_rebound_expired_entry_count': 3, 'maturity_status_counts': {'pending_future_quotes': 2457, 'matured_no_entry': 384, 'matured_labeled': 261}, 'entry_reason_counts': {'next_open': 588, 'gap_fade_condition_not_met': 261, 'pullback_not_touched': 213, 'breakout_trigger_touched': 188, 'pullback_limit_touched': 669, 'breakout_not_touched': 400, 'missing_next_quote': 648, 'gap_fade_limit_touched': 33, 'bottom_rebound_next_open': 34, 'bottom_rebound_signal_close_retest_touched': 34, 'bottom_rebound_atr_pullback_touched': 33, 'bottom_rebound_atr_pullback_not_touched': 1}, 'policy_exit_reason_counts': {'need_5_quotes': 327, 'gap_fade_condition_not_met': 261, 'pullback_not_touched': 213, 'need_10_quotes': 991, 'trailing_after_mfe_stop': 38, 'mae_stop_touched': 223, 'breakout_not_touched': 400, 'missing_next_quote': 648, 'bottom_rebound_atr_pullback_not_touched': 1}, 'source_quality_status_counts': {'pending_future_quotes': 2457, 'ok': 645}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `38` | `11.493466` | `2.60064` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 261, 'source_quality_adjusted_ev_pct': -0.762563}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `33` | `8.430048` | `-3.0` | `0.666667` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `136` | `-1.741234` | `-3.0` | `0.095588` |
| `close_below_stop` | `92` | `-2.663568` | `-3.0` | `0.032609` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `18` | `11.534985` | `-3.0` | `0.722222` |
| `below_entry_recovery_observation` | `5` | `5.73023` | `-0.772871` | `0.8` |
| `neutral_location_observation` | `7` | `3.037302` | `-3.0` | `0.428571` |
| `premium_entry_continuation_observation` | `3` | `1.8168` | `-0.808` | `0.666667` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `pullback_retest_observation` | `136` | `-1.741234` | `-3.0` | `0.095588` |
| `invalidation_observation` | `92` | `-2.663568` | `-3.0` | `0.032609` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Medicaments` | `14` | `-3.0` | `-3.0` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `10` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `9` | `-3.0` | `-3.0` |
| `sector` | `Insurance` | `9` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Iron and Steel` | `8` | `-3.0` | `-3.0` |
| `sector` | `Activities Auxiliary to Financial Service Activities` | `7` | `-3.0` | `-3.0` |
| `sector` | `Building of Ships and Boats` | `6` | `-3.0` | `-3.0` |
| `sector` | `Heavy Construction` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `6` | `-3.0` | `-3.0` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `8` | `-3.0` | `-3.0` |
| `theme_tags` | `증권` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `13` | `-2.435232` | `-3.0` |
| `sector` | `Other Financial Intermediation` | `13` | `-1.835171` | `-3.0` |
| `position_tag` | `nan` | `27` | `-1.679641` | `-3.0` |
| `theme_tags` | `스마트 그리드` | `5` | `-1.552474` | `-3.0` |
| `position_tag` | `MIDDLE` | `79` | `-1.356681` | `-3.0` |
| `sector` | `Manufacture of Basic Precious and Non-ferrous Metals` | `7` | `-1.195626` | `-3.0` |
| `theme_tags` | `NaN` | `19` | `-1.165562` | `-3.0` |
| `theme_tags` | `-` | `112` | `-1.128478` | `-3.0` |
| `block_reason` | `blocked_gatekeeper_reject` | `11` | `-1.09702` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
