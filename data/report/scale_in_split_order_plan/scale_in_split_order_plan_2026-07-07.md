# Scale-In Split Order Plan 2026-07-07

- schema_version: `scale_in_split_order_plan_v1`
- source_quality: `pass`
- runtime_apply_allowed: `True`
- policy_version: `scale_in_split_order_plan:2026-07-07:be68bc9cdeb4`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_2026-07-07.json`
- candidate_count: `2`
- counterfactual_selected_count: `2`
- baseline_fallback_count: `0`
- price_observation_join_gap_count: `0`
- market_qty_split_only_count: `0`

## Candidate Grid
- bucket=`unknown_strategy:late_loss_retry:normal` mode=`counterfactual_tick_band_selector` real=`1` sim=`0` offsets=`[0, 2]`
- bucket=`unknown_strategy:late_loss_retry:normal` mode=`diagnostic_three_leg_tick_band` real=`1` sim=`0` offsets=`[0, 1, 2]`
- bucket=`unknown_strategy:stop_line_touch:normal` mode=`counterfactual_tick_band_selector` real=`4` sim=`0` offsets=`[0, 2]`
