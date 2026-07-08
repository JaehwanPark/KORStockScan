# Scale-In Split Order Plan 2026-07-08

- schema_version: `scale_in_split_order_plan_v1`
- source_quality: `warning`
- runtime_apply_allowed: `True`
- policy_version: `scale_in_split_order_plan:2026-07-08:5f089f20f4b3`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_2026-07-08.json`
- candidate_count: `3`
- counterfactual_selected_count: `1`
- baseline_fallback_count: `2`
- price_observation_join_gap_count: `0`
- market_qty_split_only_count: `0`

## Candidate Grid
- bucket=`unknown_strategy:reversal_add_ok:normal` mode=`bounded_equal_scale_in_split_baseline` real=`0` sim=`1` offsets=`[0, 1]`
- bucket=`unknown_strategy:scalp_sim_scale_in_order_unfilled:normal` mode=`bounded_equal_scale_in_split_baseline` real=`0` sim=`1` offsets=`[0, 1]`
- bucket=`unknown_strategy:stop_line_touch:normal` mode=`counterfactual_tick_band_selector` real=`6` sim=`0` offsets=`[0, 1]`
