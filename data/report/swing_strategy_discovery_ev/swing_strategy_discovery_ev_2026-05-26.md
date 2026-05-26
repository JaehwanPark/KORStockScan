# Swing Strategy Discovery EV - 2026-05-26

- generated_at: `2026-05-26T16:26:06`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `200` / `1600` / `1600`
- labeled_sample_count: `71`
- pending_future_quote_count: `1434`
- bottom_rebound_policy_exit_row_count: `0`
- bottom_rebound_label_status_counts: `{}`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `0`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 1088, 'EXITED': 71, 'EXPIRED': 95, 'ENTERED': 346}, 'label_status_counts': {'pending_future_quotes': 1434, 'labeled': 71, 'expired_entry_no_trigger': 95}, 'bottom_rebound_label_status_counts': {}, 'bottom_rebound_maturity_status_counts': {}, 'bottom_rebound_pending_future_quote_count': 0, 'bottom_rebound_labeled_sample_count': 0, 'bottom_rebound_expired_entry_count': 0, 'maturity_status_counts': {'pending_future_quotes': 1434, 'matured_labeled': 71, 'matured_no_entry': 95}, 'entry_reason_counts': {'pullback_not_touched': 270, 'breakout_trigger_touched': 182, 'gap_fade_condition_not_met': 95, 'next_open': 200, 'pullback_limit_touched': 30, 'breakout_not_touched': 18, 'gap_fade_limit_touched': 5, 'missing_next_quote': 800}, 'policy_exit_reason_counts': {'pullback_not_touched': 270, 'trailing_after_mfe_stop': 62, 'gap_fade_condition_not_met': 95, 'need_10_quotes': 241, 'need_5_quotes': 105, 'mae_stop_touched': 9, 'breakout_not_touched': 18, 'missing_next_quote': 800}, 'source_quality_status_counts': {'pending_future_quotes': 1434, 'ok': 166}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `62` | `8.674287` | `2.45579` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 71, 'source_quality_adjusted_ev_pct': 7.27907}`

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| - | - | 0 | - | - |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
