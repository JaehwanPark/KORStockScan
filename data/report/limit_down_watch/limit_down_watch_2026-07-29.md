# Limit-Down Watch Report — 2026-07-29

- generated_at: `2026-07-30T12:03:37.393569`
- status: `pass`
- registered_code_count: `3`
- snapshot_code_count: `2`
- ordered_intraday_path_capture: `2`
- sim_candidate_ready: `False`
- real_trading_ready: `False`
- decision: `collect_source_then_build_sim_candidate`

## Blockers

- `ordered_intraday_path_capture_incomplete`
- `multi_day_cohort_sample_floor_not_established`
- `counterfactual_entry_exit_labels_missing`
- `clean_baseline_rolling_ev_missing`
- `sim_policy_catalog_handoff_missing`
- `post_sim_attribution_missing`
- `separate_live_conversion_approval_missing`

## Cohort / Price Band

| cohort | price_band | registered | snapshots | unlocked | relocked | ordered_path_capture_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| consecutive_limit_down_2plus | 1000_4999 | 1 | 0 | 0 | 0 | 0.0 |
| single_limit_down | 5000_9999 | 2 | 2 | 2 | 0 | 100.0 |

## Contract

- decision_authority: `limit_down_source_observation_only`
- runtime_effect: `False`
- actual_order_submitted: `False`
- broker_order_forbidden: `True`
- allowed_sim_apply: `False`
- allowed_runtime_apply: `False`
