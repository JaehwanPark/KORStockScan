# Swing Strategy Discovery EV - 2026-05-22

- generated_at: `2026-05-22T17:02:58`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate/arm/policy_exit_rows: `150` / `1200` / `1200`
- labeled_sample_count: `32`
- pending_future_quote_count: `1118`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `1`
- source_quality_summary: `{'implementation_status': 'implemented', 'implementation_provenance': {'order_id': 'order_swing_strategy_discovery_source_quality_followup', 'scope': 'source_quality_instrumentation_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'decision_authority': 'swing_sim_exploration_only'}, 'implementation_checks': [{'name': 'label_maturity_provenance', 'status': 'pass', 'fields': ['label_maturity_status', 'entry_reason', 'policy_exit_reason', 'future_quote_count', 'quotes_from_entry_count']}, {'name': 'source_only_contract', 'status': 'pass', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}], 'runtime_effect': False, 'decision_authority': 'swing_sim_exploration_only', 'arm_status_counts': {'PENDING_ENTRY': 898, 'ENTERED': 220, 'EXITED': 32, 'EXPIRED': 50}, 'label_status_counts': {'pending_future_quotes': 1118, 'labeled': 32, 'expired_entry_no_trigger': 50}, 'maturity_status_counts': {'pending_future_quotes': 1118, 'matured_labeled': 32, 'matured_no_entry': 50}, 'entry_reason_counts': {'next_open': 100, 'pullback_not_touched': 66, 'breakout_trigger_touched': 68, 'gap_fade_condition_not_met': 50, 'pullback_limit_touched': 84, 'breakout_not_touched': 32, 'missing_next_quote': 800}, 'policy_exit_reason_counts': {'need_5_quotes': 50, 'need_10_quotes': 170, 'pullback_not_touched': 66, 'trailing_after_mfe_stop': 15, 'gap_fade_condition_not_met': 50, 'mae_stop_touched': 17, 'breakout_not_touched': 32, 'missing_next_quote': 800}, 'source_quality_status_counts': {'pending_future_quotes': 1118, 'ok': 82}}`
- warnings: `['pending_future_quotes']`

## Surviving Arms

| arm_id | sample | source_quality_ev | downside_p10 | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `arm05_breakout_conf_trailing` | `15` | `9.93861` | `4.77324` | `1.0` |

## Legacy vs Discovery

- legacy_ml: `{}`
- discovery_combined: `{'sample_count': 32, 'source_quality_adjusted_ev_pct': 2.831309}`

## Avoid Buckets

| axis | key | sample | source_quality_ev | downside_p10 |
| --- | --- | ---: | ---: | ---: |
| `position_tag` | `BOTTOM` | `14` | `-1.159073` | `-3.0` |

## Contract

- This report is source-only and cannot mutate runtime env.
- Sim discovery labels are not real execution quality evidence.
- Sector/theme fields are diversity/source-quality inputs only.
