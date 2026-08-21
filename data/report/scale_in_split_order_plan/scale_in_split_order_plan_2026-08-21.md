# Scale-In Split Order Plan 2026-08-21

- schema_version: `scale_in_split_order_plan_v1`
- source_quality: `warning`
- runtime_apply_allowed: `False`
- policy_version: `scale_in_split_order_plan:2026-08-21:ba01b82f1996`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_2026-08-21.json`
- candidate_count: `2`
- counterfactual_selected_count: `1`
- baseline_fallback_count: `1`
- price_observation_join_gap_count: `0`
- market_qty_split_only_count: `0`

## Candidate Grid
- bucket=`scalping:scale_in_order_submitted:rising_missed` mode=`counterfactual_tick_band_selector` real=`1` sim=`0` offsets=`[0, 1]`
- bucket=`unknown_strategy:shallow_volatility_avg_down:rising_missed` mode=`bounded_equal_scale_in_split_baseline` real=`0` sim=`1` offsets=`[0, 1]`
