# Entry Split Order Plan - 2026-07-22

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `2`
- runtime_apply_allowed: `True`
- baseline_runtime_defaults_enabled: `True`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-07-22.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`20/1` ev=`None` bucket_ev=`-1.1933` observed_split_outcomes=`3` apply_scope=`baseline_split_structure` p75_down_ticks=`7.0` cancel=`0.0` pass=`True`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`22/0` ev=`None` bucket_ev=`-0.9878` observed_split_outcomes=`9` apply_scope=`none` p75_down_ticks=`14.5` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`121/1226` ev=`None` bucket_ev=`1.4417` observed_split_outcomes=`3` apply_scope=`baseline_split_structure` p75_down_ticks=`0.0` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/1` ev=`None` bucket_ev=`None` observed_split_outcomes=`0` apply_scope=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
