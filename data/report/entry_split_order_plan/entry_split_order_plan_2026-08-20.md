# Entry Split Order Plan - 2026-08-20

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `1`
- runtime_apply_allowed: `True`
- baseline_runtime_defaults_enabled: `True`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-08-20.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`10/11` ev=`None` bucket_ev=`-0.8846` observed_split_outcomes=`10` apply_scope=`none` p75_down_ticks=`0.5` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`33/0` ev=`None` bucket_ev=`0.048` observed_split_outcomes=`33` apply_scope=`none` p75_down_ticks=`37.0` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`204/2355` ev=`None` bucket_ev=`-0.2332` observed_split_outcomes=`22` apply_scope=`baseline_split_structure` p75_down_ticks=`1.25` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`0/16` ev=`None` bucket_ev=`None` observed_split_outcomes=`0` apply_scope=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
