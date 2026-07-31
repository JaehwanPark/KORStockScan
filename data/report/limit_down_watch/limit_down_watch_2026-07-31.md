# Limit-Down Watch Report — 2026-07-31

- generated_at: `2026-08-01T00:35:32.080542`
- status: `source_blocked`
- registered_code_count: `0`
- snapshot_code_count: `0`
- ordered_intraday_path_capture: `0`
- sim_candidate_ready: `False`
- real_trading_ready: `False`
- decision: `collect_source_then_build_sim_candidate`

## Blockers

- `candidate_source_quality_missing`
- `ordered_intraday_path_sample_missing`
- `ordered_intraday_path_capture_missing`
- `multi_day_cohort_sample_floor_not_established`
- `counterfactual_entry_exit_labels_missing`
- `clean_baseline_rolling_ev_missing`
- `sim_policy_catalog_handoff_missing`
- `post_sim_attribution_missing`
- `separate_live_conversion_approval_missing`

## Cohort / Price Band

| cohort | price_band | registered | snapshots | unlocked | relocked | ordered_path_capture_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |

## Contract

- decision_authority: `limit_down_source_observation_only`
- runtime_effect: `False`
- actual_order_submitted: `False`
- broker_order_forbidden: `True`
- allowed_sim_apply: `False`
- allowed_runtime_apply: `False`
