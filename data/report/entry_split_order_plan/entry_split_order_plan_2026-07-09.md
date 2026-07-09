# Entry Split Order Plan - 2026-07-09

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `1`
- runtime_apply_allowed: `False`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-07-09.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`11/1` ev=`None` bucket_ev=`None` p75_down_ticks=`1.5` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`0/0` ev=`None` bucket_ev=`None` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`40/2020` ev=`None` bucket_ev=`0.055` p75_down_ticks=`8.0` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`0/19` ev=`None` bucket_ev=`None` p75_down_ticks=`None` cancel=`0.0` pass=`False`
