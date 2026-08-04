# Scale-In Split Order Plan 2026-08-04

- schema_version: `scale_in_split_order_plan_v1`
- source_quality: `pass`
- runtime_apply_allowed: `False`
- policy_version: `scale_in_split_order_plan:2026-08-04:7c997a750a3b`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_2026-08-04.json`
- candidate_count: `3`
- counterfactual_selected_count: `3`
- baseline_fallback_count: `0`
- price_observation_join_gap_count: `2`
- market_qty_split_only_count: `0`

## Candidate Grid
- bucket=`scalping:scale_in_order_submitted:rising_missed` mode=`counterfactual_tick_band_selector` real=`2` sim=`0` offsets=`[0, 1]`
- bucket=`scalping:scale_in_order_submitted:rising_missed` mode=`diagnostic_three_leg_tick_band` real=`2` sim=`0` offsets=`[0, 1, 2]`
- bucket=`unknown_strategy:late_loss_retry:normal` mode=`counterfactual_tick_band_selector` real=`2` sim=`0` offsets=`[0, 1]`
- bucket=`unknown_strategy:late_loss_retry:normal` mode=`diagnostic_three_leg_tick_band` real=`2` sim=`0` offsets=`[0, 1, 2]`
- bucket=`unknown_strategy:late_loss_retry:rising_missed` mode=`counterfactual_tick_band_selector` real=`2` sim=`2` offsets=`[0, 1]`
- bucket=`unknown_strategy:late_loss_retry:rising_missed` mode=`diagnostic_three_leg_tick_band` real=`2` sim=`2` offsets=`[0, 1, 2]`
