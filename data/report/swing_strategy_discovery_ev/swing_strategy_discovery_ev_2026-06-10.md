# Swing Strategy Discovery EV - 2026-06-10

- generated_at: `2026-06-10T16:16:14`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `396` / `2560` / `2560`
- labeled_sample_count: `245`
- pending_future_quote_count: `2147`
- bottom_rebound_policy_exit_row_count: `416`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 368, 'labeled': 45, 'expired_entry_no_trigger': 3}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1181, 'EXPIRED': 168, 'ENTERED': 966, 'EXITED': 245}, 'label_status_counts': {'pending_future_quotes': 2147, 'expired_entry_no_trigger': 168, 'labeled': 245}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 368, 'labeled': 45, 'expired_entry_no_trigger': 3}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 368, 'matured_labeled': 45, 'matured_no_entry': 3}, 'bottom_rebound_pending_future_quote_count': 368, 'bottom_rebound_labeled_sample_count': 45, 'bottom_rebound_expired_entry_count': 3, 'maturity_status_counts': {'pending_future_quotes': 2147, 'matured_no_entry': 168, 'matured_labeled': 245}, 'entry_reason_counts': {'pullback_not_touched': 72, 'gap_fade_condition_not_met': 168, 'breakout_trigger_touched': 118, 'breakout_not_touched': 240, 'bottom_rebound_next_open': 101, 'bottom_rebound_signal_close_retest_touched': 84, 'bottom_rebound_atr_pullback_touched': 74, 'bottom_rebound_signal_close_retest_not_touched': 17, 'bottom_rebound_atr_pullback_not_touched': 27, 'pullback_limit_touched': 465, 'next_open': 358, 'gap_fade_limit_touched': 11, 'missing_next_quote': 825}, 'policy_exit_reason_counts': {'pullback_not_touched': 72, 'gap_fade_condition_not_met': 168, 'need_10_quotes': 776, 'breakout_not_touched': 240, 'bottom_rebound_signal_close_retest_not_touched': 17, 'bottom_rebound_atr_pullback_not_touched': 27, 'mae_stop_touched': 214, 'need_5_quotes': 190, 'trailing_after_mfe_stop': 31, 'missing_next_quote': 825}, 'source_quality_status_counts': {'pending_future_quotes': 2147, 'ok': 413}}`
- warnings: `['pending_future_quotes', 'clean_tuning_baseline_swing_discovery_lookback_filtered']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `31` | `8.335337` | `2.707704` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{'selection_arm': 'legacy_ml', 'sample_count': 3, 'total_row_count': 24, 'entry_fill_rate': 0.125, 'expired_rate': 0.125, 'equal_weight_avg_final_return_pct': -3.0, 'notional_weighted_ev_pct': -3.0, 'source_quality_adjusted_ev_pct': -1.8, 'diagnostic_win_rate': 0.0, 'downside_p10_pct': -3.0, 'mae_p90_pct': -5.036545}`
- discovery_combined: `{'sample_count': 242, 'source_quality_adjusted_ev_pct': -1.028932}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `25` | `5.605815` | `-3.0` | `0.44` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `145` | `-1.724142` | `-3.0` | `0.117241` |
| `close_below_stop` | `75` | `-2.140581` | `-3.0` | `0.04` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `9` | `8.130054` | `-3.0` | `0.444444` |
| `below_entry_recovery_observation` | `12` | `6.699765` | `-3.0` | `0.583333` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `premium_entry_continuation_observation` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `1` | `-0.6` | `-3.0` | `0.0` |
| `pullback_retest_observation` | `145` | `-1.724142` | `-3.0` | `0.117241` |
| `discount_entry_observation` | `3` | `-1.8` | `-3.0` | `0.0` |
| `invalidation_observation` | `75` | `-2.140581` | `-3.0` | `0.04` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Medicaments` | `11` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `9` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Iron and Steel` | `7` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of General Purpose Machinery` | `7` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Telecommunication and Broadcasting Apparatuses` | `6` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Basic Chemicals` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `반도체_생산` | `8` | `-3.0` | `-3.0` |
| `block_reason` | `blocked_gatekeeper_reject` | `18` | `-2.372067` | `-3.0` |
| `sector` | `Other Financial Intermediation` | `35` | `-2.04844` | `-3.0` |
| `position_tag` | `MIDDLE` | `49` | `-1.929937` | `-3.0` |
| `sector` | `Manufacture of Electronic Components` | `28` | `-1.872938` | `-3.0` |
| `position_tag` | `BOTTOM` | `102` | `-1.539017` | `-3.0` |
| `block_reason` | `blocked_swing_score_vpw` | `15` | `-1.534049` | `-3.0` |
| `sector` | `Data Processing, Hosting and Related activities; Web Portals` | `7` | `-1.37097` | `-3.0` |
| `theme_tags` | `-` | `96` | `-1.293118` | `-3.0` |
| `volatility_bucket` | `low` | `245` | `-1.049758` | `-3.0` |
| `block_reason` | `no_block_observed` | `203` | `-0.933123` | `-3.0` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `8` | `-0.822201` | `-3.0` |
| `position_tag` | `nan` | `58` | `-0.780824` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `10` | `-0.765278` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
