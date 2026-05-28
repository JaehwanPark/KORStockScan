# Swing Strategy Discovery EV - 2026-05-28

- generated_at: `2026-05-28T13:09:00`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `375` / `2854` / `2854`
- labeled_sample_count: `165`
- pending_future_quote_count: `2483`
- bottom_rebound_policy_exit_row_count: `126`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 126}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `12`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'ENTERED': 918, 'EXITED': 165, 'PENDING_ENTRY': 1565, 'EXPIRED': 206}, 'label_status_counts': {'pending_future_quotes': 2483, 'labeled': 165, 'expired_entry_no_trigger': 206}, 'bottom_rebound_label_status_counts': {'pending_future_quotes': 126}, 'bottom_rebound_maturity_status_counts': {'pending_future_quotes': 126}, 'bottom_rebound_pending_future_quote_count': 126, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'pending_future_quotes': 2483, 'matured_labeled': 165, 'matured_no_entry': 206}, 'entry_reason_counts': {'next_open': 468, 'pullback_not_touched': 303, 'breakout_trigger_touched': 188, 'gap_fade_condition_not_met': 206, 'pullback_limit_touched': 399, 'breakout_not_touched': 280, 'gap_fade_limit_touched': 28, 'missing_next_quote': 982}, 'policy_exit_reason_counts': {'need_5_quotes': 262, 'need_10_quotes': 656, 'pullback_not_touched': 303, 'trailing_after_mfe_stop': 46, 'gap_fade_condition_not_met': 206, 'breakout_not_touched': 280, 'mae_stop_touched': 119, 'missing_next_quote': 982}, 'source_quality_status_counts': {'pending_future_quotes': 2483, 'ok': 371}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `46` | `9.358174` | `3.153246` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 165, 'source_quality_adjusted_ev_pct': 0.365259}`

## Morning Turbulence Observation

- analysis_role: `source_only_observation`
- metric_contract: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'swing_sim_exploration_only', 'window_policy': 'rolling_90d', 'sample_floor': 5, 'sample_floor_behavior': 'hold_sample', 'primary_decision_metric': 'source_quality_adjusted_ev_pct', 'source_quality_gate': 'label_status_labeled_and_source_quality_status_ok', 'runtime_effect': False, 'allowed_runtime_apply': False, 'actual_order_submitted': False, 'broker_order_forbidden': True, 'forbidden_uses': ['time_hard_gate', 'broker_order_submit', 'runtime_threshold_apply', 'stop_relaxation_or_tightening', 'swing_dry_run_guard_change', 'real_canary_approval_standalone', 'volatile_symbol_exclusion']}`

| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `no_touch` | `38` | `8.668754` | `2.585913` | `0.921053` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `wick_stop_recovered_close_above_stop` | `55` | `-0.844029` | `-3.0` | `0.163636` |
| `close_below_stop` | `72` | `-2.691234` | `-3.0` | `0.027778` |

| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `momentum_chase_observation` | `25` | `11.755275` | `3.505418` | `1.0` |
| `below_entry_recovery_observation` | `8` | `5.006597` | `1.248234` | `0.875` |
| `premium_entry_continuation_observation` | `3` | `0.766544` | `-1.841141` | `0.666667` |
| `not_entered_or_pending` | `0` | `0.0` | `None` | `0.0` |
| `discount_entry_observation` | `0` | `0.0` | `None` | `0.0` |
| `neutral_location_observation` | `2` | `-0.148435` | `-2.490031` | `0.5` |
| `pullback_retest_observation` | `55` | `-0.844029` | `-3.0` | `0.163636` |
| `invalidation_observation` | `72` | `-2.691234` | `-3.0` | `0.027778` |

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `sector` | `Manufacture of Basic Chemicals` | `6` | `-3.0` | `-3.0` |
| `sector` | `Real Estate Activities with Own or Leased Property` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `LCD_부품,LED,무선충전기관련주` | `5` | `-3.0` | `-3.0` |
| `theme_tags` | `2차전지_소재(양극화물질등)` | `5` | `-3.0` | `-3.0` |
| `sector` | `Manufacture of Semiconductor` | `8` | `-1.767071` | `-3.0` |
| `sector` | `Manufacture of Medicaments` | `9` | `-1.605574` | `-3.0` |
| `block_reason` | `blocked_gatekeeper_reject` | `12` | `-1.440153` | `-3.0` |
| `sector` | `Other Financial Intermediation` | `11` | `-1.175218` | `-3.0` |
| `theme_tags` | `-` | `86` | `-0.744438` | `-3.0` |
| `sector` | `Manufacture of Other Chemical Products` | `12` | `-0.725628` | `-3.0` |
| `block_reason` | `blocked_swing_score_vpw` | `5` | `-0.583238` | `-3.0` |
| `position_tag` | `BOTTOM` | `47` | `-0.248951` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
