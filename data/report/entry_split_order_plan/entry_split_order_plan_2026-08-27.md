# Entry Split Order Plan - 2026-08-27

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `1`
- runtime_apply_allowed: `True`
- exploration_seed_allowed: `True` / count: `1`
- ev_validated_runtime_apply_allowed: `False` / count: `0`
- runtime_apply_authority_classes: `['bounded_exploration_seed']`
- baseline_runtime_defaults_enabled: `True`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-08-27.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`11/16` ev=`None` bucket_ev=`-0.7918` observed_split_outcomes=`11` apply_scope=`none` apply_authority=`none` p75_down_ticks=`0.0` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`40/0` ev=`None` bucket_ev=`0.0306` observed_split_outcomes=`40` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`253/2295` ev=`None` bucket_ev=`-0.1612` observed_split_outcomes=`23` apply_scope=`baseline_split_structure` apply_authority=`bounded_exploration_seed` p75_down_ticks=`6.5` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/37` ev=`None` bucket_ev=`None` observed_split_outcomes=`0` apply_scope=`none` apply_authority=`none` p75_down_ticks=`13.0` cancel=`0.0` pass=`False`
