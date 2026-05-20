# Swing Strategy Discovery EV - 2026-05-20

- generated_at: `2026-05-20T17:26:10`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `50` / `400` / `400`
- labeled_sample_count: `0`
- pending_future_quote_count: `400`
- top_surviving_arm: `-`
- avoid_bucket_count: `0`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 400}, 'label_status_counts': {'pending_future_quotes': 400}, 'maturity_status_counts': {'pending_future_quotes': 400}, 'entry_reason_counts': {'missing_next_quote': 400}, 'policy_exit_reason_counts': {'missing_next_quote': 400}, 'source_quality_status_counts': {'pending_future_quotes': 400}}`
- warnings: `['pending_future_quotes', 'sample_floor_not_met']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| - | 0 | - | - | - |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 0, 'source_quality_adjusted_ev_pct': 0.0}`

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| - | - | 0 | - | - |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
