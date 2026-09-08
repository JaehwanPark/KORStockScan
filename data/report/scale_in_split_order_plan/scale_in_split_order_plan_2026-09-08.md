# Scale-In Split Order Plan 2026-09-08

- schema_version: `scale_in_split_order_plan_v3`
- source_quality: `warning`
- runtime_apply_allowed: `False`
- policy_version: `scale_in_split_order_plan:2026-09-08:dfef4ae66496`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_2026-09-08.json`
- candidate_count: `1`
- counterfactual_selected_count: `0`
- baseline_fallback_count: `0`
- price_observation_join_gap_count: `0`
- market_qty_split_only_count: `1`

## Candidate Grid
- bucket=`scalping:late_loss_retry:normal` mode=`market_qty_split_only` real=`1` sim=`0` offsets=`market`
